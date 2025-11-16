"""
Document metadata model for chatPDF application.

This module defines the Document model for storing document metadata
and the query_analytics model for tracking query performance.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Index
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional

from .database import Base


class Document(Base):
    """
    Document metadata model.

    Stores metadata about uploaded documents including file information,
    chunking details, and embedding configuration.
    """

    __tablename__ = "documents"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # File information
    filename = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(Integer, nullable=False)

    # Processing information
    num_chunks = Column(Integer, nullable=True)
    num_pages = Column(Integer, nullable=True)

    # Embedding and indexing
    embedding_model = Column(String(100), nullable=False)
    index_path = Column(Text, nullable=True)

    # Timestamp
    created_at = Column(DateTime, nullable=False, default=func.now())

    # Indexes
    __table_args__ = (
        Index('idx_documents_filename', 'filename'),
        Index('idx_documents_created_at', 'created_at'),
    )

    def __repr__(self) -> str:
        """String representation of Document."""
        return f"<Document(id={self.id}, filename='{self.filename}', type='{self.file_type}')>"

    def to_dict(self) -> dict:
        """
        Convert document to dictionary.

        Returns:
            Dictionary representation of the document
        """
        return {
            'id': self.id,
            'filename': self.filename,
            'file_path': self.file_path,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'num_chunks': self.num_chunks,
            'num_pages': self.num_pages,
            'embedding_model': self.embedding_model,
            'index_path': self.index_path,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class QueryAnalytics(Base):
    """
    Query analytics model.

    Tracks query performance metrics including model used, tokens,
    cost, latency, and RAG strategy.
    """

    __tablename__ = "query_analytics"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Query information
    query = Column(Text, nullable=False)
    model = Column(String(100), nullable=False)
    embedding_model = Column(String(100), nullable=True)
    rag_strategy = Column(String(50), nullable=True)

    # Performance metrics
    tokens_used = Column(Integer, nullable=True)
    cost = Column(Integer, nullable=True)  # Store in cents to avoid floating point issues
    latency_ms = Column(Integer, nullable=True)
    num_results = Column(Integer, nullable=True)

    # Timestamp
    timestamp = Column(DateTime, nullable=False, default=func.now())

    # Indexes
    __table_args__ = (
        Index('idx_query_analytics_timestamp', 'timestamp'),
        Index('idx_query_analytics_model', 'model'),
    )

    def __repr__(self) -> str:
        """String representation of QueryAnalytics."""
        return f"<QueryAnalytics(id={self.id}, model='{self.model}', latency={self.latency_ms}ms)>"

    def to_dict(self) -> dict:
        """
        Convert query analytics to dictionary.

        Returns:
            Dictionary representation of the query analytics
        """
        return {
            'id': self.id,
            'query': self.query,
            'model': self.model,
            'embedding_model': self.embedding_model,
            'rag_strategy': self.rag_strategy,
            'tokens_used': self.tokens_used,
            'cost': self.cost / 100.0 if self.cost is not None else None,  # Convert cents to dollars
            'latency_ms': self.latency_ms,
            'num_results': self.num_results,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
