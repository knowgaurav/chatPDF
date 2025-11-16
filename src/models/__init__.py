"""
Models package for chatPDF application.

This package contains all database models and database connection setup.
"""

from .database import Base, Database, db, init_db, get_db
from .document import Document, QueryAnalytics
from .chat import ChatMessage

__all__ = [
    # Database
    'Base',
    'Database',
    'db',
    'init_db',
    'get_db',
    # Models
    'Document',
    'QueryAnalytics',
    'ChatMessage',
]
