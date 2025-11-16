"""
Chat message model for chatPDF application.

This module defines the ChatMessage model for storing conversation history
with documents, including message content, sources, and performance metrics.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional, List, Dict, Any
import json

from .database import Base


class ChatMessage(Base):
    """
    Chat message model.

    Stores conversation messages between user and assistant, including
    source citations, model information, and performance metrics.
    """

    __tablename__ = "chat_messages"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign key to documents
    document_id = Column(
        Integer,
        ForeignKey('documents.id', ondelete='CASCADE'),
        nullable=True  # Nullable to allow general chat without specific document
    )

    # Message content
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)

    # Source citations (stored as JSON string)
    sources = Column(Text, nullable=True)

    # Model and performance metrics
    model_used = Column(String(100), nullable=True)
    tokens_used = Column(Integer, nullable=True)
    cost = Column(Integer, nullable=True)  # Store in cents to avoid floating point issues
    latency_ms = Column(Integer, nullable=True)

    # Timestamp
    created_at = Column(DateTime, nullable=False, default=func.now())

    # Relationship to Document
    document = relationship(
        "Document",
        backref="chat_messages",
        foreign_keys=[document_id]
    )

    # Indexes
    __table_args__ = (
        Index('idx_chat_messages_document_id', 'document_id'),
        Index('idx_chat_messages_created_at', 'created_at'),
    )

    def __repr__(self) -> str:
        """String representation of ChatMessage."""
        return f"<ChatMessage(id={self.id}, role='{self.role}', document_id={self.document_id})>"

    def set_sources(self, sources: List[Dict[str, Any]]) -> None:
        """
        Set sources from a list of dictionaries.

        Args:
            sources: List of source dictionaries
        """
        if sources:
            self.sources = json.dumps(sources)
        else:
            self.sources = None

    def get_sources(self) -> Optional[List[Dict[str, Any]]]:
        """
        Get sources as a list of dictionaries.

        Returns:
            List of source dictionaries or None if no sources
        """
        if self.sources:
            try:
                return json.loads(self.sources)
            except json.JSONDecodeError:
                return None
        return None

    def to_dict(self) -> dict:
        """
        Convert chat message to dictionary.

        Returns:
            Dictionary representation of the chat message
        """
        return {
            'id': self.id,
            'document_id': self.document_id,
            'role': self.role,
            'content': self.content,
            'sources': self.get_sources(),
            'model_used': self.model_used,
            'tokens_used': self.tokens_used,
            'cost': self.cost / 100.0 if self.cost is not None else None,  # Convert cents to dollars
            'latency_ms': self.latency_ms,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    @staticmethod
    def create_user_message(
        content: str,
        document_id: Optional[int] = None
    ) -> 'ChatMessage':
        """
        Create a user message.

        Args:
            content: Message content
            document_id: Optional document ID

        Returns:
            ChatMessage instance
        """
        return ChatMessage(
            role='user',
            content=content,
            document_id=document_id
        )

    @staticmethod
    def create_assistant_message(
        content: str,
        document_id: Optional[int] = None,
        sources: Optional[List[Dict[str, Any]]] = None,
        model_used: Optional[str] = None,
        tokens_used: Optional[int] = None,
        cost: Optional[float] = None,
        latency_ms: Optional[int] = None
    ) -> 'ChatMessage':
        """
        Create an assistant message.

        Args:
            content: Message content
            document_id: Optional document ID
            sources: Optional list of source citations
            model_used: LLM model name
            tokens_used: Number of tokens used
            cost: Cost in dollars
            latency_ms: Latency in milliseconds

        Returns:
            ChatMessage instance
        """
        message = ChatMessage(
            role='assistant',
            content=content,
            document_id=document_id,
            model_used=model_used,
            tokens_used=tokens_used,
            cost=int(cost * 100) if cost is not None else None,  # Convert dollars to cents
            latency_ms=latency_ms
        )

        if sources:
            message.set_sources(sources)

        return message
