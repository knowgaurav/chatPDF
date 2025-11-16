#!/usr/bin/env python3
"""
Database initialization script for chatPDF application.

This script creates the database and all tables as specified in the LLD.
Run this script to set up the database before starting the application.

Usage:
    python init_db.py
"""

import sys
from pathlib import Path
from sqlalchemy import inspect

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.models import init_db, db, Document, ChatMessage, QueryAnalytics


def main():
    """Initialize the database and create all tables."""
    print("=" * 60)
    print("chatPDF Database Initialization")
    print("=" * 60)
    print()

    try:
        # Initialize database
        print("Creating database and tables...")
        init_db()
        print()

        # Verify tables were created
        print("Verifying tables...")
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()

        print(f"✓ Found {len(tables)} tables:")
        for table in tables:
            print(f"  - {table}")
            # Show columns for each table
            columns = inspector.get_columns(table)
            print(f"    Columns: {len(columns)}")
            for col in columns:
                print(f"      • {col['name']} ({col['type']})")
            # Show indexes
            indexes = inspector.get_indexes(table)
            if indexes:
                print(f"    Indexes: {len(indexes)}")
                for idx in indexes:
                    print(f"      • {idx['name']}")
        print()

        print("=" * 60)
        print("Database initialization completed successfully!")
        print("=" * 60)
        print()
        print("Database location:", db.engine.url)
        print()
        print("You can now start using the chatPDF application.")

    except Exception as e:
        print(f"✗ Error initializing database: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
