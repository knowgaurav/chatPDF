"""Vector store and embeddings service for chatPDF system.

This module handles vector store creation, embedding generation, similarity search,
and FAISS index management.
Based on LLD Section 4.4.
"""

import os
import pickle
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
import asyncio
import numpy as np

# FAISS for vector search
try:
    import faiss
except ImportError:
    faiss = None

# LangChain embeddings
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings

# For type hints
from .document_service import DocumentChunk


@dataclass
class VectorIndex:
    """Represents a vector index for a document."""

    document_id: str
    index_path: str
    num_vectors: int
    dimension: int
    embedding_model: str
    created_at: str


@dataclass
class SearchResult:
    """Represents a search result from vector similarity search."""

    chunk_id: str
    document_id: str
    text: str
    score: float
    metadata: Dict[str, Any]
    chunk_index: int


class EmbeddingService:
    """Service for generating embeddings using various models.

    Supports:
    - OpenAI embeddings (text-embedding-ada-002, text-embedding-3-small, etc.)
    - HuggingFace models (all-MiniLM-L6-v2, all-mpnet-base-v2, etc.)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the EmbeddingService.

        Args:
            config: Configuration dictionary containing:
                - default_model: Default embedding model to use
                - openai_api_key: OpenAI API key (if using OpenAI models)
                - cache_dir: Directory for caching models
        """
        self.config = config or {}
        self.default_model = self.config.get('default_model', 'text-embedding-ada-002')
        self.models_cache: Dict[str, Any] = {}

    def _get_embedding_model(self, model_name: str) -> Any:
        """Get or create an embedding model instance.

        Args:
            model_name: Name of the embedding model

        Returns:
            Embedding model instance
        """
        if model_name in self.models_cache:
            return self.models_cache[model_name]

        # OpenAI models
        if model_name.startswith('text-embedding'):
            api_key = self.config.get('openai_api_key', os.getenv('OPENAI_API_KEY'))
            if not api_key:
                raise ValueError("OpenAI API key required for OpenAI embeddings")

            model = OpenAIEmbeddings(
                model=model_name,
                openai_api_key=api_key
            )

        # HuggingFace models
        else:
            cache_dir = self.config.get('cache_dir', './data/models')
            model = HuggingFaceEmbeddings(
                model_name=model_name,
                cache_folder=cache_dir,
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )

        self.models_cache[model_name] = model
        return model

    async def embed(
        self,
        text: str,
        model: Optional[str] = None
    ) -> np.ndarray:
        """Generate embedding for a single text.

        Args:
            text: Text to embed
            model: Model name (uses default if None)

        Returns:
            Embedding vector as numpy array
        """
        model_name = model or self.default_model
        embedding_model = self._get_embedding_model(model_name)

        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None,
            embedding_model.embed_query,
            text
        )

        return np.array(embedding, dtype=np.float32)

    async def embed_batch(
        self,
        texts: List[str],
        model: Optional[str] = None,
        batch_size: int = 100
    ) -> np.ndarray:
        """Generate embeddings for multiple texts in batches.

        Args:
            texts: List of texts to embed
            model: Model name (uses default if None)
            batch_size: Number of texts to process at once

        Returns:
            Array of embeddings with shape (len(texts), embedding_dim)
        """
        model_name = model or self.default_model
        embedding_model = self._get_embedding_model(model_name)

        all_embeddings = []

        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            # Run in thread pool
            loop = asyncio.get_event_loop()
            batch_embeddings = await loop.run_in_executor(
                None,
                embedding_model.embed_documents,
                batch
            )

            all_embeddings.extend(batch_embeddings)

        return np.array(all_embeddings, dtype=np.float32)

    def get_embedding_dimension(self, model: Optional[str] = None) -> int:
        """Get the dimension of embeddings for a model.

        Args:
            model: Model name (uses default if None)

        Returns:
            Embedding dimension
        """
        model_name = model or self.default_model

        # Known dimensions for common models
        model_dimensions = {
            'text-embedding-ada-002': 1536,
            'text-embedding-3-small': 1536,
            'text-embedding-3-large': 3072,
            'all-MiniLM-L6-v2': 384,
            'all-mpnet-base-v2': 768,
            'BAAI/bge-small-en-v1.5': 384,
            'BAAI/bge-base-en-v1.5': 768,
        }

        # Return known dimension or detect from model
        if model_name in model_dimensions:
            return model_dimensions[model_name]

        # Embed a test string to get dimension
        embedding_model = self._get_embedding_model(model_name)
        test_embedding = embedding_model.embed_query("test")
        return len(test_embedding)


class VectorService:
    """Service for vector store management and similarity search.

    Responsibilities:
    - Create and manage FAISS indices
    - Similarity search
    - Index persistence (save/load)
    - Support for different embedding models
    """

    def __init__(
        self,
        embedding_service: Optional[EmbeddingService] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """Initialize the VectorService.

        Args:
            embedding_service: EmbeddingService instance
            config: Configuration dictionary containing:
                - vector_store_path: Directory for storing indices
                - index_type: Type of FAISS index ('flat', 'ivf', 'hnsw')
        """
        self.config = config or {}
        self.embedding_service = embedding_service or EmbeddingService(config)
        self.vector_store_path = Path(
            self.config.get('vector_store_path', './data/vector_stores')
        )
        self.vector_store_path.mkdir(parents=True, exist_ok=True)

        # Cache for loaded indices
        self.indices_cache: Dict[str, Dict[str, Any]] = {}

        # Verify FAISS is available
        if faiss is None:
            raise ImportError(
                "FAISS is required for vector operations. "
                "Install with: pip install faiss-cpu or pip install faiss-gpu"
            )

    async def create_index(
        self,
        document_id: str,
        chunks: List[DocumentChunk],
        embedding_model: str = "text-embedding-ada-002"
    ) -> VectorIndex:
        """Create a vector index for document chunks.

        Args:
            document_id: Unique document identifier
            chunks: List of document chunks to index
            embedding_model: Name of embedding model to use

        Returns:
            VectorIndex object with index metadata

        Raises:
            ValueError: If chunks list is empty
        """
        if not chunks:
            raise ValueError("Cannot create index from empty chunks list")

        # Generate embeddings for all chunks
        chunk_texts = [chunk.text for chunk in chunks]
        embeddings = await self.embedding_service.embed_batch(
            chunk_texts,
            model=embedding_model
        )

        # Create FAISS index
        index, dimension = self._create_faiss_index(embeddings)

        # Create metadata mapping
        metadata = {
            'chunks': chunks,
            'embedding_model': embedding_model,
            'dimension': dimension
        }

        # Persist index
        index_path = self._persist_index(document_id, index, metadata)

        # Cache the index
        self.indices_cache[document_id] = {
            'index': index,
            'metadata': metadata
        }

        return VectorIndex(
            document_id=document_id,
            index_path=index_path,
            num_vectors=len(embeddings),
            dimension=dimension,
            embedding_model=embedding_model,
            created_at=str(np.datetime64('now'))
        )

    async def similarity_search(
        self,
        query: str,
        document_ids: List[str],
        top_k: int = 10,
        score_threshold: Optional[float] = None
    ) -> List[SearchResult]:
        """Perform semantic similarity search across documents.

        Args:
            query: Search query text
            document_ids: List of document IDs to search
            top_k: Number of top results to return
            score_threshold: Minimum similarity score (optional)

        Returns:
            List of SearchResult objects sorted by relevance

        Raises:
            ValueError: If no valid document indices found
        """
        if not document_ids:
            raise ValueError("Must provide at least one document_id")

        all_results = []

        for doc_id in document_ids:
            # Load index for this document
            index_data = self._load_index(doc_id)
            if not index_data:
                continue  # Skip if index not found

            index = index_data['index']
            metadata = index_data['metadata']
            chunks = metadata['chunks']
            embedding_model = metadata['embedding_model']

            # Generate query embedding using same model as index
            query_embedding = await self.embedding_service.embed(
                query,
                model=embedding_model
            )

            # Reshape for FAISS (needs 2D array)
            query_vector = query_embedding.reshape(1, -1)

            # Search index
            distances, indices = index.search(query_vector, min(top_k, len(chunks)))

            # Convert results
            for dist, idx in zip(distances[0], indices[0]):
                if idx < 0 or idx >= len(chunks):
                    continue  # Skip invalid indices

                # Convert distance to similarity score (L2 distance -> similarity)
                # Lower distance = higher similarity
                score = 1.0 / (1.0 + dist)

                # Filter by threshold if provided
                if score_threshold and score < score_threshold:
                    continue

                chunk = chunks[idx]
                result = SearchResult(
                    chunk_id=chunk.chunk_id,
                    document_id=doc_id,
                    text=chunk.text,
                    score=float(score),
                    metadata=chunk.metadata,
                    chunk_index=chunk.chunk_index
                )
                all_results.append(result)

        # Sort by score (descending) and return top_k
        all_results.sort(key=lambda x: x.score, reverse=True)
        return all_results[:top_k]

    async def delete_index(self, document_id: str) -> bool:
        """Delete a vector index.

        Args:
            document_id: ID of document whose index to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            # Remove from cache
            if document_id in self.indices_cache:
                del self.indices_cache[document_id]

            # Delete index file
            index_path = self.vector_store_path / f"{document_id}.index"
            if index_path.exists():
                index_path.unlink()

            # Delete metadata file
            metadata_path = self.vector_store_path / f"{document_id}.metadata"
            if metadata_path.exists():
                metadata_path.unlink()

            return True
        except Exception as e:
            print(f"Error deleting index for {document_id}: {str(e)}")
            return False

    def _create_faiss_index(
        self,
        embeddings: np.ndarray
    ) -> Tuple[faiss.Index, int]:
        """Create an optimized FAISS index.

        Selects index type based on dataset size:
        - Small (<1000): Flat (exact search)
        - Medium (1000-100k): IVF (approximate search)
        - Large (>100k): HNSW (hierarchical approximate search)

        Args:
            embeddings: Array of embeddings with shape (n_samples, dimension)

        Returns:
            Tuple of (FAISS index, embedding dimension)
        """
        n_samples, dimension = embeddings.shape

        if n_samples < 1000:
            # Use flat index for small datasets (exact search)
            index = faiss.IndexFlatL2(dimension)

        elif n_samples < 100000:
            # Use IVF for medium datasets
            nlist = int(np.sqrt(n_samples))  # Number of clusters
            quantizer = faiss.IndexFlatL2(dimension)
            index = faiss.IndexIVFFlat(quantizer, dimension, nlist)

            # Train index
            index.train(embeddings)

        else:
            # Use HNSW for large datasets
            index = faiss.IndexHNSWFlat(dimension, 32)  # 32 = M parameter
            index.hnsw.efConstruction = 40

        # Add vectors to index
        index.add(embeddings)

        return index, dimension

    def _persist_index(
        self,
        document_id: str,
        index: faiss.Index,
        metadata: Dict[str, Any]
    ) -> str:
        """Save FAISS index and metadata to disk.

        Args:
            document_id: Document identifier
            index: FAISS index to save
            metadata: Metadata to save alongside index

        Returns:
            Path to saved index file
        """
        # Save FAISS index
        index_path = self.vector_store_path / f"{document_id}.index"
        faiss.write_index(index, str(index_path))

        # Save metadata
        metadata_path = self.vector_store_path / f"{document_id}.metadata"
        with open(metadata_path, 'wb') as f:
            pickle.dump(metadata, f)

        return str(index_path)

    def _load_index(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Load FAISS index and metadata from disk.

        Args:
            document_id: Document identifier

        Returns:
            Dictionary with 'index' and 'metadata' keys, or None if not found
        """
        # Check cache first
        if document_id in self.indices_cache:
            return self.indices_cache[document_id]

        # Load from disk
        index_path = self.vector_store_path / f"{document_id}.index"
        metadata_path = self.vector_store_path / f"{document_id}.metadata"

        if not index_path.exists() or not metadata_path.exists():
            return None

        try:
            # Load FAISS index
            index = faiss.read_index(str(index_path))

            # Load metadata
            with open(metadata_path, 'rb') as f:
                metadata = pickle.load(f)

            # Cache for future use
            index_data = {
                'index': index,
                'metadata': metadata
            }
            self.indices_cache[document_id] = index_data

            return index_data

        except Exception as e:
            print(f"Error loading index for {document_id}: {str(e)}")
            return None

    def get_index_stats(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get statistics about a vector index.

        Args:
            document_id: Document identifier

        Returns:
            Dictionary with index statistics, or None if not found
        """
        index_data = self._load_index(document_id)
        if not index_data:
            return None

        index = index_data['index']
        metadata = index_data['metadata']

        return {
            'document_id': document_id,
            'num_vectors': index.ntotal,
            'dimension': metadata['dimension'],
            'embedding_model': metadata['embedding_model'],
            'index_type': type(index).__name__,
            'is_trained': getattr(index, 'is_trained', True)
        }
