"""Hybrid search service for chatPDF system.

This module implements keyword search (BM25), hybrid search combining semantic
and keyword approaches, and query expansion.
Based on LLD Section 4.5.
"""

import pickle
from pathlib import Path
from typing import List, Dict, Optional, Any, Set
from dataclasses import dataclass
import numpy as np

# BM25 for keyword search
try:
    from rank_bm25 import BM25Okapi
except ImportError:
    BM25Okapi = None

# For type hints
from .document_service import DocumentChunk
from .vector_service import SearchResult


@dataclass
class QueryExpansion:
    """Represents an expanded query with additional terms."""

    original_query: str
    expanded_queries: List[str]
    expansion_method: str


class SearchService:
    """Service for keyword search and hybrid search strategies.

    Responsibilities:
    - BM25 keyword search
    - Hybrid search (semantic + keyword)
    - Reciprocal Rank Fusion (RRF)
    - Query expansion
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the SearchService.

        Args:
            config: Configuration dictionary containing:
                - index_path: Directory for storing BM25 indices
                - tokenizer: Custom tokenizer function (optional)
        """
        self.config = config or {}
        self.index_path = Path(
            self.config.get('index_path', './data/vector_stores')
        )
        self.index_path.mkdir(parents=True, exist_ok=True)

        # Cache for BM25 indices: document_id -> BM25 index
        self.bm25_indices: Dict[str, Dict[str, Any]] = {}

        # Verify BM25 is available
        if BM25Okapi is None:
            raise ImportError(
                "rank-bm25 is required for keyword search. "
                "Install with: pip install rank-bm25"
            )

    def create_bm25_index(
        self,
        document_id: str,
        chunks: List[DocumentChunk]
    ) -> bool:
        """Create BM25 index for keyword search.

        Args:
            document_id: Unique document identifier
            chunks: List of document chunks to index

        Returns:
            True if successful

        Raises:
            ValueError: If chunks list is empty
        """
        if not chunks:
            raise ValueError("Cannot create index from empty chunks list")

        # Tokenize all chunks
        tokenized_corpus = [self._tokenize(chunk.text) for chunk in chunks]

        # Create BM25 index
        bm25_index = BM25Okapi(tokenized_corpus)

        # Store index and metadata
        self.bm25_indices[document_id] = {
            'index': bm25_index,
            'chunks': chunks,
            'tokenized_corpus': tokenized_corpus
        }

        # Persist to disk
        self._persist_bm25_index(document_id, bm25_index, chunks)

        return True

    def keyword_search(
        self,
        query: str,
        document_ids: List[str],
        top_k: int = 10,
        score_threshold: Optional[float] = None
    ) -> List[SearchResult]:
        """Perform BM25 keyword search across documents.

        Args:
            query: Search query text
            document_ids: List of document IDs to search
            top_k: Number of top results to return
            score_threshold: Minimum BM25 score (optional)

        Returns:
            List of SearchResult objects sorted by BM25 score

        Raises:
            ValueError: If no valid document indices found
        """
        if not document_ids:
            raise ValueError("Must provide at least one document_id")

        all_results = []
        tokenized_query = self._tokenize(query)

        for doc_id in document_ids:
            # Load BM25 index
            index_data = self._load_bm25_index(doc_id)
            if not index_data:
                continue  # Skip if index not found

            bm25_index = index_data['index']
            chunks = index_data['chunks']

            # Get BM25 scores for all chunks
            scores = bm25_index.get_scores(tokenized_query)

            # Get top-k indices
            if len(scores) > top_k:
                top_indices = np.argsort(scores)[-top_k:][::-1]
            else:
                top_indices = np.argsort(scores)[::-1]

            # Create search results
            for idx in top_indices:
                score = float(scores[idx])

                # Filter by threshold if provided
                if score_threshold and score < score_threshold:
                    continue

                chunk = chunks[idx]
                result = SearchResult(
                    chunk_id=chunk.chunk_id,
                    document_id=doc_id,
                    text=chunk.text,
                    score=score,
                    metadata={**chunk.metadata, 'search_type': 'keyword'},
                    chunk_index=chunk.chunk_index
                )
                all_results.append(result)

        # Sort by score (descending) and return top_k
        all_results.sort(key=lambda x: x.score, reverse=True)
        return all_results[:top_k]

    def hybrid_search(
        self,
        semantic_results: List[SearchResult],
        keyword_results: List[SearchResult],
        alpha: float = 0.5,
        top_k: Optional[int] = None
    ) -> List[SearchResult]:
        """Fuse semantic and keyword search results using Reciprocal Rank Fusion (RRF).

        RRF formula: score(d) = sum(1 / (k + rank(d)))
        where k is a constant (typically 60) and rank(d) is the rank of document d.

        Args:
            semantic_results: Results from semantic (vector) search
            keyword_results: Results from keyword (BM25) search
            alpha: Weight for semantic results (0-1). keyword weight = 1-alpha
            top_k: Number of results to return (None = return all)

        Returns:
            List of fused SearchResult objects sorted by combined score
        """
        # Reciprocal Rank Fusion constant
        k = 60

        # Dictionary to accumulate scores: chunk_id -> (total_score, result)
        scores: Dict[str, tuple] = {}

        # Add semantic results with RRF scoring
        for rank, result in enumerate(semantic_results):
            rrf_score = alpha / (k + rank + 1)

            if result.chunk_id in scores:
                # Update existing score
                existing_score, existing_result = scores[result.chunk_id]
                scores[result.chunk_id] = (
                    existing_score + rrf_score,
                    existing_result
                )
            else:
                # Create new entry
                scores[result.chunk_id] = (rrf_score, result)

        # Add keyword results with RRF scoring
        for rank, result in enumerate(keyword_results):
            rrf_score = (1 - alpha) / (k + rank + 1)

            if result.chunk_id in scores:
                # Update existing score
                existing_score, existing_result = scores[result.chunk_id]
                scores[result.chunk_id] = (
                    existing_score + rrf_score,
                    existing_result
                )
            else:
                # Create new entry
                scores[result.chunk_id] = (rrf_score, result)

        # Sort by combined score (descending)
        sorted_items = sorted(
            scores.items(),
            key=lambda x: x[1][0],
            reverse=True
        )

        # Create final results with updated scores
        fused_results = []
        for chunk_id, (score, result) in sorted_items:
            # Create new result with fused score
            fused_result = SearchResult(
                chunk_id=result.chunk_id,
                document_id=result.document_id,
                text=result.text,
                score=score,
                metadata={**result.metadata, 'search_type': 'hybrid'},
                chunk_index=result.chunk_index
            )
            fused_results.append(fused_result)

        # Return top_k if specified
        if top_k:
            return fused_results[:top_k]
        return fused_results

    def expand_query(
        self,
        query: str,
        method: str = "synonyms",
        max_expansions: int = 3
    ) -> QueryExpansion:
        """Expand query with additional related terms.

        Args:
            query: Original query text
            method: Expansion method ("synonyms", "stemming", "ngrams")
            max_expansions: Maximum number of expanded queries to generate

        Returns:
            QueryExpansion object with original and expanded queries

        Note:
            This is a basic implementation. For production use, consider:
            - Using WordNet for synonyms
            - LLM-based query expansion
            - Domain-specific thesaurus
        """
        expanded_queries = [query]  # Always include original

        if method == "synonyms":
            # Basic synonym expansion (placeholder)
            # In production, use WordNet or LLM-based expansion
            expanded_queries.extend(
                self._expand_with_synonyms(query, max_expansions - 1)
            )

        elif method == "stemming":
            # Stemming-based expansion
            expanded_queries.extend(
                self._expand_with_stemming(query, max_expansions - 1)
            )

        elif method == "ngrams":
            # N-gram based expansion
            expanded_queries.extend(
                self._expand_with_ngrams(query, max_expansions - 1)
            )

        return QueryExpansion(
            original_query=query,
            expanded_queries=expanded_queries,
            expansion_method=method
        )

    def delete_bm25_index(self, document_id: str) -> bool:
        """Delete BM25 index for a document.

        Args:
            document_id: ID of document whose index to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            # Remove from cache
            if document_id in self.bm25_indices:
                del self.bm25_indices[document_id]

            # Delete persisted index
            index_file = self.index_path / f"{document_id}.bm25"
            if index_file.exists():
                index_file.unlink()

            return True
        except Exception as e:
            print(f"Error deleting BM25 index for {document_id}: {str(e)}")
            return False

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text for BM25 indexing.

        Args:
            text: Text to tokenize

        Returns:
            List of tokens

        Note:
            Basic whitespace tokenization. For better results, consider:
            - Lowercasing
            - Removing punctuation
            - Stemming/lemmatization
            - Stop word removal
        """
        # Check if custom tokenizer provided
        if 'tokenizer' in self.config and callable(self.config['tokenizer']):
            return self.config['tokenizer'](text)

        # Basic tokenization: lowercase and split on whitespace
        tokens = text.lower().split()

        # Remove punctuation
        import string
        tokens = [
            token.strip(string.punctuation)
            for token in tokens
            if token.strip(string.punctuation)
        ]

        return tokens

    def _persist_bm25_index(
        self,
        document_id: str,
        bm25_index: BM25Okapi,
        chunks: List[DocumentChunk]
    ) -> None:
        """Save BM25 index to disk.

        Args:
            document_id: Document identifier
            bm25_index: BM25 index to save
            chunks: Document chunks
        """
        index_file = self.index_path / f"{document_id}.bm25"

        data = {
            'index': bm25_index,
            'chunks': chunks
        }

        with open(index_file, 'wb') as f:
            pickle.dump(data, f)

    def _load_bm25_index(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Load BM25 index from disk or cache.

        Args:
            document_id: Document identifier

        Returns:
            Dictionary with 'index' and 'chunks' keys, or None if not found
        """
        # Check cache first
        if document_id in self.bm25_indices:
            return self.bm25_indices[document_id]

        # Load from disk
        index_file = self.index_path / f"{document_id}.bm25"
        if not index_file.exists():
            return None

        try:
            with open(index_file, 'rb') as f:
                data = pickle.load(f)

            # Cache for future use
            self.bm25_indices[document_id] = data
            return data

        except Exception as e:
            print(f"Error loading BM25 index for {document_id}: {str(e)}")
            return None

    def _expand_with_synonyms(
        self,
        query: str,
        max_expansions: int
    ) -> List[str]:
        """Expand query with synonyms (basic implementation).

        Args:
            query: Original query
            max_expansions: Maximum number of expansions

        Returns:
            List of expanded queries
        """
        # Placeholder implementation
        # In production, use WordNet or LLM-based expansion
        expanded = []

        # Example: simple word replacements
        common_synonyms = {
            'document': ['file', 'paper', 'text'],
            'find': ['search', 'locate', 'discover'],
            'summary': ['overview', 'abstract', 'synopsis'],
            'explain': ['describe', 'clarify', 'elaborate'],
        }

        words = query.lower().split()
        for word in words:
            if word in common_synonyms and len(expanded) < max_expansions:
                for synonym in common_synonyms[word][:max_expansions - len(expanded)]:
                    # Replace word with synonym
                    expanded_query = query.lower().replace(word, synonym)
                    if expanded_query != query.lower():
                        expanded.append(expanded_query)

        return expanded[:max_expansions]

    def _expand_with_stemming(
        self,
        query: str,
        max_expansions: int
    ) -> List[str]:
        """Expand query with stemmed variants.

        Args:
            query: Original query
            max_expansions: Maximum number of expansions

        Returns:
            List of expanded queries
        """
        # Placeholder implementation
        # In production, use NLTK PorterStemmer or similar
        expanded = []

        # Simple suffix removal
        suffixes = ['ing', 'ed', 's', 'es', 'er', 'est']
        words = query.split()

        for i, word in enumerate(words):
            for suffix in suffixes:
                if word.endswith(suffix) and len(expanded) < max_expansions:
                    stemmed_word = word[:-len(suffix)]
                    if len(stemmed_word) > 2:  # Avoid very short stems
                        expanded_words = words.copy()
                        expanded_words[i] = stemmed_word
                        expanded.append(' '.join(expanded_words))

        return expanded[:max_expansions]

    def _expand_with_ngrams(
        self,
        query: str,
        max_expansions: int
    ) -> List[str]:
        """Expand query with n-gram variants.

        Args:
            query: Original query
            max_expansions: Maximum number of expansions

        Returns:
            List of expanded queries
        """
        # Generate bigrams and trigrams from query
        expanded = []
        words = query.split()

        # Bigrams
        if len(words) >= 2:
            for i in range(len(words) - 1):
                bigram = f"{words[i]} {words[i+1]}"
                if bigram not in expanded and len(expanded) < max_expansions:
                    expanded.append(bigram)

        # Trigrams
        if len(words) >= 3:
            for i in range(len(words) - 2):
                trigram = f"{words[i]} {words[i+1]} {words[i+2]}"
                if trigram not in expanded and len(expanded) < max_expansions:
                    expanded.append(trigram)

        return expanded[:max_expansions]

    def get_index_stats(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get statistics about a BM25 index.

        Args:
            document_id: Document identifier

        Returns:
            Dictionary with index statistics, or None if not found
        """
        index_data = self._load_bm25_index(document_id)
        if not index_data:
            return None

        bm25_index = index_data['index']
        chunks = index_data['chunks']

        return {
            'document_id': document_id,
            'num_chunks': len(chunks),
            'avg_doc_length': bm25_index.avgdl,
            'index_type': 'BM25Okapi'
        }

    def rerank_results(
        self,
        results: List[SearchResult],
        query: str,
        method: str = "score_boost"
    ) -> List[SearchResult]:
        """Re-rank search results using various strategies.

        Args:
            results: Initial search results
            query: Original query
            method: Re-ranking method ("score_boost", "diversity", "recency")

        Returns:
            Re-ranked list of SearchResult objects
        """
        if method == "score_boost":
            # Boost scores for results containing exact query terms
            query_terms = set(self._tokenize(query))
            reranked = []

            for result in results:
                result_terms = set(self._tokenize(result.text))
                overlap = len(query_terms.intersection(result_terms))
                boost_factor = 1.0 + (overlap * 0.1)  # 10% boost per matching term

                boosted_result = SearchResult(
                    chunk_id=result.chunk_id,
                    document_id=result.document_id,
                    text=result.text,
                    score=result.score * boost_factor,
                    metadata={**result.metadata, 'boost_factor': boost_factor},
                    chunk_index=result.chunk_index
                )
                reranked.append(boosted_result)

            reranked.sort(key=lambda x: x.score, reverse=True)
            return reranked

        elif method == "diversity":
            # Promote diversity by penalizing similar consecutive results
            if not results:
                return results

            diverse_results = [results[0]]  # Always include top result
            used_chunks: Set[str] = {results[0].chunk_id}

            for result in results[1:]:
                # Simple diversity: avoid adjacent chunks from same document
                if result.chunk_id not in used_chunks:
                    # Check if not adjacent to recently added chunks
                    is_diverse = True
                    for recent in diverse_results[-3:]:  # Check last 3 results
                        if (result.document_id == recent.document_id and
                                abs(result.chunk_index - recent.chunk_index) <= 1):
                            is_diverse = False
                            break

                    if is_diverse:
                        diverse_results.append(result)
                        used_chunks.add(result.chunk_id)

            return diverse_results

        else:
            # Default: return as-is
            return results
