"""
Database connection and session management for chatPDF application.

This module sets up SQLite database connection using SQLAlchemy ORM.
"""

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from typing import Generator
import os
from pathlib import Path

# Base class for all models
Base = declarative_base()

# Database configuration
DATABASE_DIR = Path(__file__).parent.parent.parent / "data"
DATABASE_PATH = DATABASE_DIR / "chatpdf.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"


class Database:
    """Database connection manager."""

    def __init__(self, database_url: str = DATABASE_URL):
        """
        Initialize database connection.

        Args:
            database_url: SQLite database URL
        """
        # Create data directory if it doesn't exist
        DATABASE_DIR.mkdir(parents=True, exist_ok=True)

        # Create engine with SQLite-specific settings
        self.engine = create_engine(
            database_url,
            echo=False,  # Set to True for SQL query logging
            connect_args={"check_same_thread": False},  # SQLite specific
            pool_pre_ping=True,
        )

        # Enable foreign key constraints for SQLite
        @event.listens_for(self.engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        # Create session factory
        self.SessionLocal = scoped_session(
            sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
        )

    def create_tables(self) -> None:
        """Create all database tables."""
        Base.metadata.create_all(bind=self.engine)

    def drop_tables(self) -> None:
        """Drop all database tables."""
        Base.metadata.drop_all(bind=self.engine)

    def get_session(self) -> Generator:
        """
        Get database session.

        Yields:
            SQLAlchemy session
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def close(self) -> None:
        """Close database connection."""
        self.SessionLocal.remove()


# Global database instance
db = Database()


def init_db() -> None:
    """Initialize database and create all tables."""
    db.create_tables()
    print(f"Database initialized at: {DATABASE_PATH}")


def get_db() -> Generator:
    """
    Dependency function for getting database session.

    Yields:
        Database session
    """
    yield from db.get_session()


if __name__ == "__main__":
    # Initialize database when run directly
    init_db()
