# Database Models Documentation

This directory contains all database models and database connection setup for the chatPDF application.

## Structure

### Files

1. **database.py** - Database connection and session management
   - SQLite connection setup using SQLAlchemy ORM
   - Database session factory and context manager
   - Base class for all models
   - Database initialization utilities

2. **document.py** - Document metadata models
   - `Document` model - Stores document metadata, file information, and indexing details
   - `QueryAnalytics` model - Tracks query performance metrics

3. **chat.py** - Chat message model
   - `ChatMessage` model - Stores conversation history with source citations and performance metrics

4. **__init__.py** - Package initialization
   - Exports all models and database utilities

## Database Schema

### documents Table
Stores metadata about uploaded documents.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key (auto-increment) |
| filename | VARCHAR(255) | Original filename |
| file_path | TEXT | Path to stored file |
| file_type | VARCHAR(50) | File type (pdf, docx, txt, md) |
| file_size | INTEGER | File size in bytes |
| num_chunks | INTEGER | Number of text chunks created |
| num_pages | INTEGER | Number of pages in document |
| embedding_model | VARCHAR(100) | Model used for embeddings |
| index_path | TEXT | Path to FAISS index file |
| created_at | DATETIME | Creation timestamp |

**Indexes:**
- `idx_documents_filename` on `filename`
- `idx_documents_created_at` on `created_at` (DESC)

### chat_messages Table
Stores conversation messages between user and assistant.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key (auto-increment) |
| document_id | INTEGER | Foreign key to documents table |
| role | VARCHAR(20) | Message role ('user' or 'assistant') |
| content | TEXT | Message content |
| sources | TEXT | JSON string with source citations |
| model_used | VARCHAR(100) | LLM model name |
| tokens_used | INTEGER | Number of tokens used |
| cost | INTEGER | Cost in cents (to avoid floating point issues) |
| latency_ms | INTEGER | Response latency in milliseconds |
| created_at | DATETIME | Creation timestamp |

**Indexes:**
- `idx_chat_messages_document_id` on `document_id`
- `idx_chat_messages_created_at` on `created_at` (DESC)

**Foreign Keys:**
- `document_id` REFERENCES `documents(id)` ON DELETE CASCADE

### query_analytics Table
Tracks query performance and analytics.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key (auto-increment) |
| query | TEXT | User query text |
| model | VARCHAR(100) | LLM model used |
| embedding_model | VARCHAR(100) | Embedding model used |
| rag_strategy | VARCHAR(50) | RAG strategy (hybrid, semantic, keyword, etc.) |
| tokens_used | INTEGER | Number of tokens used |
| cost | INTEGER | Cost in cents |
| latency_ms | INTEGER | Query latency in milliseconds |
| num_results | INTEGER | Number of results returned |
| timestamp | DATETIME | Query timestamp |

**Indexes:**
- `idx_query_analytics_timestamp` on `timestamp` (DESC)
- `idx_query_analytics_model` on `model`

## Usage

### Initializing the Database

Run the initialization script from the project root:

```bash
python init_db.py
```

This will:
1. Create the SQLite database at `data/chatpdf.db`
2. Create all tables with proper schema and indexes
3. Verify the database structure

### Using Models in Code

```python
from src.models import db, Document, ChatMessage, QueryAnalytics

# Get a database session
session = next(db.get_session())

# Create a new document
doc = Document(
    filename="example.pdf",
    file_path="/path/to/example.pdf",
    file_type="pdf",
    file_size=1024000,
    embedding_model="text-embedding-ada-002"
)
session.add(doc)
session.commit()

# Query documents
documents = session.query(Document).all()

# Create a chat message
message = ChatMessage.create_user_message(
    content="What is this document about?",
    document_id=doc.id
)
session.add(message)
session.commit()

# Create an assistant response
response = ChatMessage.create_assistant_message(
    content="This document is about...",
    document_id=doc.id,
    sources=[{"page": 1, "text": "..."}],
    model_used="gpt-3.5-turbo",
    tokens_used=150,
    cost=0.0003,
    latency_ms=1200
)
session.add(response)
session.commit()
```

### Working with Sources

The `ChatMessage` model provides helper methods for working with JSON sources:

```python
# Set sources
message = ChatMessage(role="assistant", content="Answer...")
message.set_sources([
    {"page": 1, "text": "Source text...", "score": 0.95},
    {"page": 2, "text": "More context...", "score": 0.87}
])

# Get sources
sources = message.get_sources()  # Returns list of dicts
```

## Important Notes

1. **Cost Storage**: Costs are stored as integers in cents to avoid floating-point precision issues. Use the `to_dict()` method to get the cost in dollars.

2. **Foreign Key Constraints**: SQLite foreign key constraints are enabled in the database configuration. When a document is deleted, all associated chat messages are automatically deleted (CASCADE).

3. **Session Management**: Always use the context manager or properly close sessions to avoid connection leaks:
   ```python
   for session in db.get_session():
       # Your code here
       pass  # Session is automatically committed and closed
   ```

4. **Thread Safety**: The database uses `scoped_session` for thread-safe session management.

## Testing

The models include `to_dict()` methods for easy serialization and testing:

```python
doc = Document(filename="test.pdf", ...)
doc_dict = doc.to_dict()
# Returns: {'id': 1, 'filename': 'test.pdf', ...}
```

## Migration Notes

When making changes to the schema:
1. Update the model classes
2. Drop and recreate tables (for development): `db.drop_tables()` then `db.create_tables()`
3. For production, use a migration tool like Alembic (to be implemented)
