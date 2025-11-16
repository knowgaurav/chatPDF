"""
RAG Service - Advanced Retrieval-Augmented Generation Pipeline

Implements advanced RAG techniques:
- Multi-query generation
- Hybrid search (semantic + keyword)
- Re-ranking with cross-encoder
- Contextual compression
- Source attribution
"""

import logging
import time
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

from sentence_transformers import CrossEncoder
import numpy as np

from ..providers.base_provider import Message, GenerationConfig

logger = logging.getLogger(__name__)


@dataclass
class Source:
    """Source citation for retrieved context"""
    document_id: str
    document_name: str
    chunk_id: str
    chunk_text: str
    page: Optional[int] = None
    score: float = 0.0
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class SearchResult:
    """Result from search operation"""
    chunk_id: str
    document_id: str
    text: str
    score: float
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class QueryResult:
    """Result from RAG query"""
    answer: str
    sources: List[Source]
    model: str
    tokens_used: int
    cost: float
    latency_ms: int
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class RAGConfig:
    """Configuration for RAG pipeline"""
    # Retrieval
    top_k: int = 10
    use_hybrid_search: bool = True
    hybrid_alpha: float = 0.5  # Weight for semantic vs keyword (0=keyword, 1=semantic)

    # Multi-query
    use_multi_query: bool = True
    num_queries: int = 3

    # Re-ranking
    use_reranking: bool = True
    rerank_top_k: int = 5

    # Compression
    use_compression: bool = False
    compression_ratio: float = 0.5

    # Generation
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    max_tokens: int = 500


class RAGService:
    """
    Advanced RAG pipeline service

    Orchestrates retrieval, re-ranking, compression, and generation
    """

    # Prompt templates
    MULTI_QUERY_PROMPT = """You are an AI assistant helping to generate alternative search queries.

Given the original query, generate {num_queries} different ways to ask the same question.
These variations should help retrieve relevant documents from different angles.

Original query: {query}

Generate {num_queries} alternative queries (one per line):"""

    QA_PROMPT = """You are a helpful AI assistant. Answer the question based on the provided context.

Context:
{context}

Question: {question}

Instructions:
- Answer based only on the provided context
- If the context doesn't contain enough information, say so
- Be concise and accurate
- Cite specific parts of the context when relevant

Answer:"""

    def __init__(
        self,
        vector_service,
        search_service,
        llm_service,
        config: Optional[RAGConfig] = None
    ):
        """
        Initialize RAG service

        Args:
            vector_service: Vector/embedding service for semantic search
            search_service: Search service for keyword search
            llm_service: LLM service for generation
            config: RAG configuration
        """
        self.vector_service = vector_service
        self.search_service = search_service
        self.llm_service = llm_service
        self.config = config or RAGConfig()

        # Initialize re-ranker if enabled
        self.reranker = None
        if self.config.use_reranking:
            try:
                self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-12-v2')
                logger.info("Cross-encoder re-ranker initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize re-ranker: {e}")
                self.config.use_reranking = False

        logger.info("RAG service initialized")

    async def query(
        self,
        question: str,
        document_ids: Optional[List[str]] = None,
        config: Optional[RAGConfig] = None
    ) -> QueryResult:
        """
        Execute complete RAG pipeline

        Args:
            question: User's question
            document_ids: List of document IDs to search (None = all)
            config: Optional config override

        Returns:
            QueryResult with answer and sources
        """
        start_time = time.time()
        config = config or self.config

        try:
            logger.info(f"RAG query: {question[:100]}...")

            # Step 1: Multi-query generation
            queries = await self._generate_queries(question, config)
            logger.debug(f"Generated {len(queries)} query variations")

            # Step 2: Hybrid search
            results = await self._hybrid_search(queries, document_ids, config)
            logger.debug(f"Retrieved {len(results)} initial results")

            # Step 3: Re-ranking
            if config.use_reranking and self.reranker:
                results = await self._rerank(question, results, config)
                logger.debug(f"Re-ranked to top {len(results)} results")

            # Step 4: Contextual compression
            if config.use_compression:
                results = await self._compress_context(question, results, config)
                logger.debug(f"Compressed to {len(results)} results")

            # Step 5: Generate answer
            answer, generation_metadata = await self._generate_answer(
                question, results, config
            )
            logger.debug(f"Generated answer ({len(answer)} chars)")

            # Step 6: Extract sources
            sources = self._extract_sources(results)

            # Calculate total latency
            latency_ms = int((time.time() - start_time) * 1000)

            return QueryResult(
                answer=answer,
                sources=sources,
                model=config.model,
                tokens_used=generation_metadata.get("tokens_used", 0),
                cost=generation_metadata.get("cost", 0.0),
                latency_ms=latency_ms,
                metadata={
                    "num_queries": len(queries),
                    "num_results": len(results),
                    "reranked": config.use_reranking,
                    "compressed": config.use_compression,
                }
            )

        except Exception as e:
            logger.error(f"RAG query failed: {e}")
            raise

    async def _generate_queries(
        self,
        question: str,
        config: RAGConfig
    ) -> List[str]:
        """
        Generate multiple search query variations

        Args:
            question: Original question
            config: RAG configuration

        Returns:
            List of query variations (including original)
        """
        queries = [question]  # Always include original

        if not config.use_multi_query or config.num_queries <= 1:
            return queries

        try:
            # Generate query variations using LLM
            prompt = self.MULTI_QUERY_PROMPT.format(
                query=question,
                num_queries=config.num_queries - 1
            )

            generation_config = GenerationConfig(
                temperature=0.7,
                max_tokens=200
            )

            result = await self.llm_service.generate(
                prompt=prompt,
                model=config.model,
                generation_config=generation_config
            )

            # Parse generated queries (one per line)
            generated = [
                q.strip()
                for q in result.text.strip().split('\n')
                if q.strip() and not q.strip().startswith('#')
            ]

            # Add to queries list (limit to num_queries total)
            queries.extend(generated[:config.num_queries - 1])

        except Exception as e:
            logger.warning(f"Multi-query generation failed: {e}, using original only")

        return queries

    async def _hybrid_search(
        self,
        queries: List[str],
        document_ids: Optional[List[str]],
        config: RAGConfig
    ) -> List[SearchResult]:
        """
        Perform hybrid search (semantic + keyword)

        Args:
            queries: List of query variations
            document_ids: Document IDs to search
            config: RAG configuration

        Returns:
            List of search results
        """
        all_results = {}  # chunk_id -> SearchResult

        for query in queries:
            # Semantic search (vector similarity)
            semantic_results = await self.vector_service.similarity_search(
                query=query,
                document_ids=document_ids,
                top_k=config.top_k * 2  # Retrieve more for fusion
            )

            # Add to results
            for result in semantic_results:
                chunk_id = result.get("chunk_id")
                if chunk_id not in all_results or result.get("score", 0) > all_results[chunk_id].score:
                    all_results[chunk_id] = SearchResult(
                        chunk_id=chunk_id,
                        document_id=result.get("document_id", ""),
                        text=result.get("text", ""),
                        score=result.get("score", 0.0),
                        metadata=result.get("metadata", {})
                    )

            # Keyword search (BM25) if hybrid enabled
            if config.use_hybrid_search and hasattr(self.search_service, 'keyword_search'):
                try:
                    keyword_results = await self.search_service.keyword_search(
                        query=query,
                        document_ids=document_ids,
                        top_k=config.top_k * 2
                    )

                    # Merge with semantic results
                    for result in keyword_results:
                        chunk_id = result.get("chunk_id")
                        if chunk_id in all_results:
                            # Combine scores with alpha weight
                            all_results[chunk_id].score = (
                                config.hybrid_alpha * all_results[chunk_id].score +
                                (1 - config.hybrid_alpha) * result.get("score", 0.0)
                            )
                        else:
                            all_results[chunk_id] = SearchResult(
                                chunk_id=chunk_id,
                                document_id=result.get("document_id", ""),
                                text=result.get("text", ""),
                                score=(1 - config.hybrid_alpha) * result.get("score", 0.0),
                                metadata=result.get("metadata", {})
                            )

                except Exception as e:
                    logger.warning(f"Keyword search failed: {e}, using semantic only")

        # Sort by score and return top-k
        sorted_results = sorted(
            all_results.values(),
            key=lambda x: x.score,
            reverse=True
        )

        return sorted_results[:config.top_k]

    async def _rerank(
        self,
        question: str,
        results: List[SearchResult],
        config: RAGConfig
    ) -> List[SearchResult]:
        """
        Re-rank results using cross-encoder

        Args:
            question: Original question
            results: Initial search results
            config: RAG configuration

        Returns:
            Re-ranked results
        """
        if not self.reranker or len(results) == 0:
            return results

        try:
            # Prepare pairs for cross-encoder
            pairs = [[question, result.text] for result in results]

            # Score all pairs
            scores = self.reranker.predict(pairs)

            # Update scores
            for i, score in enumerate(scores):
                results[i].score = float(score)

            # Sort by new scores and return top-k
            sorted_results = sorted(
                results,
                key=lambda x: x.score,
                reverse=True
            )

            return sorted_results[:config.rerank_top_k]

        except Exception as e:
            logger.warning(f"Re-ranking failed: {e}, using original ranking")
            return results[:config.rerank_top_k]

    async def _compress_context(
        self,
        question: str,
        results: List[SearchResult],
        config: RAGConfig
    ) -> List[SearchResult]:
        """
        Remove irrelevant parts from retrieved context

        Args:
            question: Original question
            results: Search results
            config: RAG configuration

        Returns:
            Compressed results
        """
        # For now, simple implementation: just truncate each result
        # In production, use LLM-based compression or sentence extraction

        compressed = []
        for result in results:
            # Split into sentences
            sentences = result.text.split('. ')

            # Keep first N sentences based on compression ratio
            keep_count = max(1, int(len(sentences) * config.compression_ratio))
            compressed_text = '. '.join(sentences[:keep_count])

            if not compressed_text.endswith('.'):
                compressed_text += '.'

            compressed.append(SearchResult(
                chunk_id=result.chunk_id,
                document_id=result.document_id,
                text=compressed_text,
                score=result.score,
                metadata=result.metadata
            ))

        return compressed

    async def _generate_answer(
        self,
        question: str,
        results: List[SearchResult],
        config: RAGConfig
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Generate answer using LLM with retrieved context

        Args:
            question: Original question
            results: Retrieved and processed results
            config: RAG configuration

        Returns:
            Tuple of (answer text, metadata)
        """
        # Build context from results
        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(f"[{i}] {result.text}")

        context = "\n\n".join(context_parts)

        # Build prompt
        prompt = self.QA_PROMPT.format(
            context=context,
            question=question
        )

        # Generate answer
        generation_config = GenerationConfig(
            temperature=config.temperature,
            max_tokens=config.max_tokens
        )

        result = await self.llm_service.generate(
            prompt=prompt,
            model=config.model,
            generation_config=generation_config
        )

        metadata = {
            "tokens_used": result.tokens_used,
            "cost": result.cost,
            "latency_ms": result.latency_ms,
            "context_length": len(context)
        }

        return result.text, metadata

    async def generate_answer_stream(
        self,
        question: str,
        results: List[SearchResult],
        config: RAGConfig
    ):
        """
        Generate answer with streaming

        Args:
            question: Original question
            results: Retrieved and processed results
            config: RAG configuration

        Yields:
            Text chunks as they are generated
        """
        # Build context from results
        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(f"[{i}] {result.text}")

        context = "\n\n".join(context_parts)

        # Build prompt
        prompt = self.QA_PROMPT.format(
            context=context,
            question=question
        )

        # Stream answer
        generation_config = GenerationConfig(
            temperature=config.temperature,
            max_tokens=config.max_tokens
        )

        async for chunk in self.llm_service.generate_stream(
            prompt=prompt,
            model=config.model,
            generation_config=generation_config
        ):
            yield chunk

    def _extract_sources(self, results: List[SearchResult]) -> List[Source]:
        """
        Extract source citations from results

        Args:
            results: Search results

        Returns:
            List of source citations
        """
        sources = []

        for result in results:
            source = Source(
                document_id=result.document_id,
                document_name=result.metadata.get("document_name", "Unknown") if result.metadata else "Unknown",
                chunk_id=result.chunk_id,
                chunk_text=result.text[:200] + "..." if len(result.text) > 200 else result.text,
                page=result.metadata.get("page") if result.metadata else None,
                score=result.score,
                metadata=result.metadata
            )
            sources.append(source)

        return sources

    async def query_stream(
        self,
        question: str,
        document_ids: Optional[List[str]] = None,
        config: Optional[RAGConfig] = None
    ):
        """
        Execute RAG pipeline with streaming answer generation

        Args:
            question: User's question
            document_ids: List of document IDs to search
            config: Optional config override

        Yields:
            Dict with 'type' and 'data' for different stages
        """
        config = config or self.config

        try:
            # Step 1: Multi-query generation
            yield {"type": "status", "data": "Generating query variations..."}
            queries = await self._generate_queries(question, config)
            yield {"type": "queries", "data": queries}

            # Step 2: Hybrid search
            yield {"type": "status", "data": "Searching documents..."}
            results = await self._hybrid_search(queries, document_ids, config)
            yield {"type": "results_count", "data": len(results)}

            # Step 3: Re-ranking
            if config.use_reranking and self.reranker:
                yield {"type": "status", "data": "Re-ranking results..."}
                results = await self._rerank(question, results, config)

            # Step 4: Contextual compression
            if config.use_compression:
                yield {"type": "status", "data": "Compressing context..."}
                results = await self._compress_context(question, results, config)

            # Step 5: Extract sources first
            sources = self._extract_sources(results)
            yield {"type": "sources", "data": [s.__dict__ for s in sources]}

            # Step 6: Stream answer
            yield {"type": "status", "data": "Generating answer..."}
            yield {"type": "answer_start", "data": None}

            async for chunk in self.generate_answer_stream(question, results, config):
                yield {"type": "answer_chunk", "data": chunk}

            yield {"type": "answer_end", "data": None}

        except Exception as e:
            logger.error(f"RAG streaming query failed: {e}")
            yield {"type": "error", "data": str(e)}
