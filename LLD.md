# Low-Level Design (LLD) - Advanced chatPDF System

## Table of Contents
1. [Project Structure](#1-project-structure)
2. [Database Schema](#2-database-schema)
3. [API Specifications](#3-api-specifications)
4. [Module Designs](#4-module-designs)
5. [Class Diagrams](#5-class-diagrams)
6. [Sequence Diagrams](#6-sequence-diagrams)
7. [Configuration Management](#7-configuration-management)
8. [Error Handling](#8-error-handling)
9. [Testing Strategy](#9-testing-strategy)

---

## 1. Project Structure

```
chatPDF/
├── backend/
│   ├── app/
│   │   ├── __init__.py                 # Flask app factory
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── routes/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── documents.py        # Document endpoints
│   │   │   │   ├── chat.py             # Chat endpoints
│   │   │   │   ├── models.py           # Model management endpoints
│   │   │   │   ├── health.py           # Health check endpoints
│   │   │   │   └── auth.py             # Authentication endpoints
│   │   │   ├── schemas/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── document.py         # Document Pydantic models
│   │   │   │   ├── chat.py             # Chat Pydantic models
│   │   │   │   └── user.py             # User Pydantic models
│   │   │   └── middleware/
│   │   │       ├── __init__.py
│   │   │       ├── auth.py             # JWT authentication
│   │   │       ├── rate_limit.py       # Rate limiting
│   │   │       └── error_handler.py    # Global error handling
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py                 # User SQLAlchemy model
│   │   │   ├── document.py             # Document SQLAlchemy model
│   │   │   ├── chat.py                 # Chat history SQLAlchemy model
│   │   │   └── session.py              # Session SQLAlchemy model
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── document_service.py     # Document processing
│   │   │   ├── rag_service.py          # RAG pipeline
│   │   │   ├── llm_service.py          # LLM management
│   │   │   ├── vector_service.py       # Vector store operations
│   │   │   ├── embedding_service.py    # Embedding generation
│   │   │   ├── chat_service.py         # Chat/conversation management
│   │   │   └── search_service.py       # Hybrid search
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── logger.py               # Logging configuration
│   │       ├── validators.py           # Input validation
│   │       ├── text_processing.py      # Text utilities
│   │       └── file_utils.py           # File operations
│   ├── config/
│   │   ├── __init__.py
│   │   ├── config.py                   # Configuration classes
│   │   └── settings.yaml               # Default settings
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py                 # Pytest fixtures
│   │   ├── test_api/
│   │   │   ├── test_documents.py
│   │   │   └── test_chat.py
│   │   ├── test_services/
│   │   │   ├── test_rag_service.py
│   │   │   └── test_llm_service.py
│   │   └── test_utils/
│   ├── migrations/                      # Alembic migrations
│   │   └── versions/
│   ├── requirements.txt                 # Core dependencies
│   ├── requirements-dev.txt             # Development dependencies
│   ├── requirements-local.txt           # Local LLM dependencies
│   └── run.py                          # Application entry point
├── frontend/
│   ├── react-app/
│   │   ├── src/
│   │   │   ├── components/
│   │   │   │   ├── Chat/
│   │   │   │   │   ├── ChatWindow.tsx
│   │   │   │   │   ├── MessageList.tsx
│   │   │   │   │   └── InputBox.tsx
│   │   │   │   ├── Documents/
│   │   │   │   │   ├── DocumentUpload.tsx
│   │   │   │   │   ├── DocumentList.tsx
│   │   │   │   │   └── DocumentViewer.tsx
│   │   │   │   ├── Settings/
│   │   │   │   │   ├── ModelSelector.tsx
│   │   │   │   │   └── RAGConfig.tsx
│   │   │   │   └── Common/
│   │   │   │       ├── Header.tsx
│   │   │   │       └── Sidebar.tsx
│   │   │   ├── services/
│   │   │   │   ├── api.ts
│   │   │   │   └── websocket.ts
│   │   │   ├── store/
│   │   │   │   ├── chatStore.ts
│   │   │   │   └── documentStore.ts
│   │   │   ├── types/
│   │   │   │   └── index.ts
│   │   │   ├── App.tsx
│   │   │   └── main.tsx
│   │   ├── package.json
│   │   └── tsconfig.json
│   └── streamlit/
│       └── app.py                      # Enhanced Streamlit app
├── data/
│   ├── uploads/                        # Uploaded documents
│   ├── vector_stores/                  # Persisted vector indices
│   └── databases/                      # SQLite database (dev)
├── docs/
│   ├── API.md                          # API documentation
│   ├── DEPLOYMENT.md                   # Deployment guide
│   └── USER_GUIDE.md                   # User manual
├── logs/                               # Application logs
├── scripts/
│   ├── init_db.py                      # Database initialization
│   ├── migrate_data.py                 # Data migration
│   └── seed_data.py                    # Seed test data
├── docker/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── Dockerfile.ollama
├── .env.example                        # Environment variables template
├── .gitignore
├── docker-compose.yml                  # Multi-container setup
├── docker-compose.dev.yml              # Development override
├── HLD.md                              # High-Level Design
├── LLD.md                              # Low-Level Design (this file)
└── README.md                           # Project documentation
```

---

## 2. Database Schema

### 2.1 Entity Relationship Diagram

```
┌─────────────────┐
│     users       │
├─────────────────┤
│ id (PK)         │
│ username        │
│ email           │
│ password_hash   │
│ api_key         │
│ created_at      │
│ updated_at      │
└─────────────────┘
        │
        │ 1:N
        │
        ▼
┌─────────────────┐
│   documents     │
├─────────────────┤
│ id (PK)         │
│ user_id (FK)    │
│ filename        │
│ file_path       │
│ file_type       │
│ file_size       │
│ status          │
│ num_chunks      │
│ vector_index_id │
│ metadata        │
│ created_at      │
│ updated_at      │
└─────────────────┘
        │
        │ 1:N
        │
        ▼
┌─────────────────┐
│  chat_sessions  │
├─────────────────┤
│ id (PK)         │
│ user_id (FK)    │
│ document_id (FK)│
│ title           │
│ created_at      │
│ updated_at      │
└─────────────────┘
        │
        │ 1:N
        │
        ▼
┌─────────────────┐
│  chat_messages  │
├─────────────────┤
│ id (PK)         │
│ session_id (FK) │
│ role            │
│ content         │
│ metadata        │
│ tokens_used     │
│ cost            │
│ created_at      │
└─────────────────┘

┌─────────────────┐
│ vector_indices  │
├─────────────────┤
│ id (PK)         │
│ document_id (FK)│
│ index_type      │
│ index_path      │
│ dimension       │
│ num_vectors     │
│ embedding_model │
│ created_at      │
└─────────────────┘

┌─────────────────┐
│ usage_analytics │
├─────────────────┤
│ id (PK)         │
│ user_id (FK)    │
│ endpoint        │
│ method          │
│ tokens_used     │
│ cost            │
│ latency_ms      │
│ status_code     │
│ timestamp       │
└─────────────────┘
```

### 2.2 Table Definitions

#### 2.2.1 users
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    api_key VARCHAR(100) UNIQUE,
    is_active BOOLEAN DEFAULT TRUE,
    role VARCHAR(20) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_api_key ON users(api_key);
```

#### 2.2.2 documents
```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'processing',  -- processing, completed, failed
    num_chunks INTEGER,
    num_pages INTEGER,
    vector_index_id UUID,
    metadata JSONB,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_documents_user_id ON documents(user_id);
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_documents_created_at ON documents(created_at DESC);
```

#### 2.2.3 chat_sessions
```sql
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    document_id UUID REFERENCES documents(id) ON DELETE SET NULL,
    title VARCHAR(255),
    config JSONB,  -- LLM model, RAG settings, etc.
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_chat_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX idx_chat_sessions_document_id ON chat_sessions(document_id);
```

#### 2.2.4 chat_messages
```sql
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,  -- user, assistant, system
    content TEXT NOT NULL,
    sources JSONB,  -- Source attribution
    metadata JSONB,
    tokens_used INTEGER,
    cost DECIMAL(10, 6),
    latency_ms INTEGER,
    model_used VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX idx_chat_messages_created_at ON chat_messages(created_at);
```

#### 2.2.5 vector_indices
```sql
CREATE TABLE vector_indices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    index_type VARCHAR(50) NOT NULL,  -- faiss, chromadb
    index_path VARCHAR(500) NOT NULL,
    dimension INTEGER NOT NULL,
    num_vectors INTEGER NOT NULL,
    embedding_model VARCHAR(100) NOT NULL,
    index_config JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_vector_indices_document_id ON vector_indices(document_id);
```

#### 2.2.6 usage_analytics
```sql
CREATE TABLE usage_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    session_id UUID,
    endpoint VARCHAR(100),
    method VARCHAR(10),
    tokens_used INTEGER,
    cost DECIMAL(10, 6),
    latency_ms INTEGER,
    status_code INTEGER,
    error_type VARCHAR(50),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_usage_analytics_user_id ON usage_analytics(user_id);
CREATE INDEX idx_usage_analytics_timestamp ON usage_analytics(timestamp DESC);
```

---

## 3. API Specifications

### 3.1 Base Configuration
- **Base URL**: `http://localhost:5000/api/v1`
- **Authentication**: Bearer Token (JWT)
- **Content-Type**: `application/json`
- **Rate Limiting**: 100 requests/minute per user

### 3.2 Authentication Endpoints

#### POST /auth/register
Register a new user.

**Request:**
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePass123!"
}
```

**Response (201):**
```json
{
  "success": true,
  "data": {
    "user_id": "uuid-here",
    "username": "john_doe",
    "email": "john@example.com",
    "api_key": "generated-api-key"
  },
  "message": "User registered successfully"
}
```

#### POST /auth/login
Authenticate user and get JWT token.

**Request:**
```json
{
  "email": "john@example.com",
  "password": "SecurePass123!"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "access_token": "jwt-token-here",
    "refresh_token": "refresh-token-here",
    "token_type": "Bearer",
    "expires_in": 3600,
    "user": {
      "id": "uuid-here",
      "username": "john_doe",
      "email": "john@example.com"
    }
  }
}
```

### 3.3 Document Management Endpoints

#### POST /documents/upload
Upload a document for processing.

**Request (multipart/form-data):**
```
file: <file-data>
metadata: {
  "title": "My Document",
  "tags": ["research", "AI"]
}
```

**Response (202):**
```json
{
  "success": true,
  "data": {
    "document_id": "uuid-here",
    "filename": "document.pdf",
    "status": "processing",
    "estimated_time": 30
  },
  "message": "Document uploaded and processing started"
}
```

#### GET /documents
List all documents for the authenticated user.

**Query Parameters:**
- `page` (default: 1)
- `limit` (default: 20)
- `status` (optional: all, processing, completed, failed)
- `sort_by` (default: created_at)
- `order` (default: desc)

**Response (200):**
```json
{
  "success": true,
  "data": {
    "documents": [
      {
        "id": "uuid-here",
        "filename": "document.pdf",
        "file_type": "application/pdf",
        "file_size": 1024000,
        "status": "completed",
        "num_chunks": 150,
        "num_pages": 20,
        "created_at": "2025-11-16T10:00:00Z",
        "updated_at": "2025-11-16T10:05:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 45,
      "pages": 3
    }
  }
}
```

#### GET /documents/{document_id}
Get document details.

**Response (200):**
```json
{
  "success": true,
  "data": {
    "id": "uuid-here",
    "filename": "document.pdf",
    "file_type": "application/pdf",
    "file_size": 1024000,
    "status": "completed",
    "num_chunks": 150,
    "num_pages": 20,
    "metadata": {
      "title": "My Document",
      "author": "John Doe",
      "created_date": "2025-01-01"
    },
    "vector_index": {
      "id": "uuid-here",
      "type": "faiss",
      "dimension": 1536,
      "num_vectors": 150
    },
    "created_at": "2025-11-16T10:00:00Z"
  }
}
```

#### DELETE /documents/{document_id}
Delete a document and its associated data.

**Response (200):**
```json
{
  "success": true,
  "message": "Document deleted successfully"
}
```

### 3.4 Chat Endpoints

#### POST /chat/sessions
Create a new chat session.

**Request:**
```json
{
  "document_ids": ["uuid-1", "uuid-2"],
  "title": "Research Discussion",
  "config": {
    "model": "gpt-4",
    "temperature": 0.7,
    "top_k": 5,
    "use_reranking": true
  }
}
```

**Response (201):**
```json
{
  "success": true,
  "data": {
    "session_id": "uuid-here",
    "title": "Research Discussion",
    "created_at": "2025-11-16T10:00:00Z"
  }
}
```

#### POST /chat/query
Ask a question (supports streaming).

**Request:**
```json
{
  "session_id": "uuid-here",
  "query": "What are the main findings?",
  "stream": true,
  "config": {
    "model": "gpt-4",
    "temperature": 0.7,
    "max_tokens": 500,
    "top_k": 5
  }
}
```

**Response (200) - Non-streaming:**
```json
{
  "success": true,
  "data": {
    "message_id": "uuid-here",
    "answer": "The main findings are...",
    "sources": [
      {
        "document_id": "uuid-here",
        "document_name": "research.pdf",
        "page": 5,
        "chunk_text": "relevant excerpt...",
        "score": 0.92
      }
    ],
    "metadata": {
      "model": "gpt-4",
      "tokens_used": 450,
      "cost": 0.0023,
      "latency_ms": 1250
    }
  }
}
```

**Response (200) - Streaming (SSE):**
```
event: start
data: {"message_id": "uuid-here"}

event: token
data: {"token": "The"}

event: token
data: {"token": " main"}

event: sources
data: {"sources": [...]}

event: end
data: {"metadata": {...}}
```

#### GET /chat/sessions/{session_id}/history
Get chat history for a session.

**Response (200):**
```json
{
  "success": true,
  "data": {
    "session_id": "uuid-here",
    "messages": [
      {
        "id": "msg-uuid-1",
        "role": "user",
        "content": "What are the main findings?",
        "created_at": "2025-11-16T10:00:00Z"
      },
      {
        "id": "msg-uuid-2",
        "role": "assistant",
        "content": "The main findings are...",
        "sources": [...],
        "metadata": {
          "tokens_used": 450,
          "cost": 0.0023
        },
        "created_at": "2025-11-16T10:00:05Z"
      }
    ]
  }
}
```

### 3.5 Model Management Endpoints

#### GET /models/available
List all available LLM models.

**Response (200):**
```json
{
  "success": true,
  "data": {
    "cloud_models": [
      {
        "id": "gpt-4-turbo",
        "provider": "openai",
        "name": "GPT-4 Turbo",
        "context_window": 128000,
        "cost_per_1k_tokens": 0.01,
        "available": true
      }
    ],
    "local_models": [
      {
        "id": "llama3:8b",
        "provider": "ollama",
        "name": "Llama 3 8B",
        "context_window": 8192,
        "cost_per_1k_tokens": 0,
        "available": true
      }
    ]
  }
}
```

#### POST /models/ollama/pull
Download a model from Ollama registry.

**Request:**
```json
{
  "model": "llama3:8b"
}
```

**Response (202):**
```json
{
  "success": true,
  "message": "Model download started",
  "data": {
    "job_id": "uuid-here",
    "status": "downloading"
  }
}
```

### 3.6 Health & Monitoring Endpoints

#### GET /health
System health check.

**Response (200):**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-16T10:00:00Z",
  "services": {
    "database": {
      "status": "up",
      "latency_ms": 5
    },
    "redis": {
      "status": "up",
      "latency_ms": 2
    },
    "vector_store": {
      "status": "up",
      "count": 1500
    },
    "ollama": {
      "status": "up",
      "models": 3
    }
  },
  "version": "2.0.0"
}
```

---

## 4. Module Designs

### 4.1 Document Service (`document_service.py`)

**Responsibilities:**
- Document upload handling
- Format detection
- Text extraction
- Chunking strategy
- Metadata extraction

**Class Structure:**
```python
class DocumentService:
    def __init__(self, config: Config):
        self.config = config
        self.extractors = {
            'pdf': PDFExtractor(),
            'docx': DocxExtractor(),
            'txt': TextExtractor(),
            'md': MarkdownExtractor()
        }

    async def upload_document(
        self,
        file: FileStorage,
        user_id: str,
        metadata: Optional[Dict] = None
    ) -> Document:
        """Upload and process document"""
        pass

    async def extract_text(
        self,
        file_path: str,
        file_type: str
    ) -> str:
        """Extract text from document"""
        pass

    def chunk_text(
        self,
        text: str,
        strategy: str = "recursive"
    ) -> List[DocumentChunk]:
        """Split text into chunks"""
        pass

    async def delete_document(
        self,
        document_id: str
    ) -> bool:
        """Delete document and associated data"""
        pass
```

**Chunking Strategies:**
1. **RecursiveCharacterTextSplitter**: Default, preserves structure
2. **SemanticChunker**: Split based on semantic similarity
3. **TokenTextSplitter**: Split by token count
4. **MarkdownHeaderTextSplitter**: Preserve markdown structure

### 4.2 RAG Service (`rag_service.py`)

**Responsibilities:**
- Orchestrate retrieval pipeline
- Hybrid search coordination
- Re-ranking
- Contextual compression
- Source attribution

**Class Structure:**
```python
class RAGService:
    def __init__(
        self,
        vector_service: VectorService,
        search_service: SearchService,
        llm_service: LLMService,
        config: RAGConfig
    ):
        self.vector_service = vector_service
        self.search_service = search_service
        self.llm_service = llm_service
        self.config = config
        self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-12-v2')

    async def query(
        self,
        question: str,
        document_ids: List[str],
        config: Optional[QueryConfig] = None
    ) -> QueryResult:
        """Execute RAG pipeline"""
        # 1. Multi-query generation
        queries = await self._generate_queries(question)

        # 2. Hybrid search
        results = await self._hybrid_search(queries, document_ids)

        # 3. Re-rank
        reranked = await self._rerank(question, results)

        # 4. Contextual compression
        compressed = await self._compress_context(question, reranked)

        # 5. Generate answer
        answer = await self._generate_answer(question, compressed)

        # 6. Extract sources
        sources = self._extract_sources(compressed, answer)

        return QueryResult(answer=answer, sources=sources)

    async def _generate_queries(
        self,
        question: str
    ) -> List[str]:
        """Generate multiple search queries"""
        pass

    async def _hybrid_search(
        self,
        queries: List[str],
        document_ids: List[str]
    ) -> List[SearchResult]:
        """Combine semantic + keyword search"""
        pass

    async def _rerank(
        self,
        question: str,
        results: List[SearchResult]
    ) -> List[SearchResult]:
        """Re-rank with cross-encoder"""
        pass

    async def _compress_context(
        self,
        question: str,
        results: List[SearchResult]
    ) -> List[SearchResult]:
        """Remove irrelevant context"""
        pass
```

### 4.3 LLM Service (`llm_service.py`)

**Responsibilities:**
- Multi-provider LLM management
- Model selection and routing
- Streaming support
- Cost tracking
- Fallback handling

**Class Structure:**
```python
class LLMService:
    def __init__(self, config: Config):
        self.config = config
        self.providers = {
            'openai': OpenAIProvider(),
            'ollama': OllamaProvider(),
            'huggingface': HuggingFaceProvider()
        }

    async def generate(
        self,
        prompt: str,
        model: str,
        stream: bool = False,
        **kwargs
    ) -> Union[str, AsyncGenerator[str, None]]:
        """Generate response from LLM"""
        provider = self._get_provider(model)

        if stream:
            return provider.generate_stream(prompt, model, **kwargs)
        else:
            return await provider.generate(prompt, model, **kwargs)

    async def chat(
        self,
        messages: List[Message],
        model: str,
        stream: bool = False,
        **kwargs
    ) -> Union[ChatResponse, AsyncGenerator[str, None]]:
        """Chat completion"""
        pass

    def _get_provider(self, model: str) -> BaseProvider:
        """Route to appropriate provider"""
        if model.startswith('gpt'):
            return self.providers['openai']
        elif model.startswith('llama') or model.startswith('mistral'):
            return self.providers['ollama']
        else:
            return self.providers['huggingface']
```

**Provider Interface:**
```python
class BaseProvider(ABC):
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        model: str,
        **kwargs
    ) -> str:
        pass

    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        model: str,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        pass

    @abstractmethod
    def calculate_cost(
        self,
        tokens: int,
        model: str
    ) -> float:
        pass
```

### 4.4 Vector Service (`vector_service.py`)

**Responsibilities:**
- Vector store management
- Embedding generation
- Similarity search
- Index persistence

**Class Structure:**
```python
class VectorService:
    def __init__(
        self,
        embedding_service: EmbeddingService,
        config: VectorConfig
    ):
        self.embedding_service = embedding_service
        self.config = config
        self.stores = {}  # document_id -> vector_store

    async def create_index(
        self,
        document_id: str,
        chunks: List[DocumentChunk],
        embedding_model: str = "text-embedding-ada-002"
    ) -> VectorIndex:
        """Create vector index for document"""
        # Generate embeddings
        embeddings = await self.embedding_service.embed_batch(
            [chunk.text for chunk in chunks],
            model=embedding_model
        )

        # Create FAISS index
        index = self._create_faiss_index(embeddings, chunks)

        # Persist index
        index_path = self._persist_index(document_id, index)

        return VectorIndex(
            document_id=document_id,
            index_path=index_path,
            num_vectors=len(embeddings)
        )

    async def similarity_search(
        self,
        query: str,
        document_ids: List[str],
        top_k: int = 10
    ) -> List[SearchResult]:
        """Semantic similarity search"""
        # Get query embedding
        query_embedding = await self.embedding_service.embed(query)

        # Search in each document
        results = []
        for doc_id in document_ids:
            index = self._load_index(doc_id)
            scores, indices = index.search(query_embedding, top_k)
            results.extend(self._format_results(doc_id, scores, indices))

        # Sort by score
        return sorted(results, key=lambda x: x.score, reverse=True)[:top_k]

    def _create_faiss_index(
        self,
        embeddings: np.ndarray,
        chunks: List[DocumentChunk]
    ) -> faiss.Index:
        """Create optimized FAISS index"""
        dimension = embeddings.shape[1]

        if len(embeddings) < 1000:
            # Use flat index for small datasets
            index = faiss.IndexFlatL2(dimension)
        else:
            # Use IVF index for larger datasets
            nlist = int(np.sqrt(len(embeddings)))
            quantizer = faiss.IndexFlatL2(dimension)
            index = faiss.IndexIVFFlat(quantizer, dimension, nlist)
            index.train(embeddings)

        index.add(embeddings)
        return index
```

### 4.5 Search Service (`search_service.py`)

**Responsibilities:**
- Keyword search (BM25)
- Result fusion
- Query expansion

**Class Structure:**
```python
from rank_bm25 import BM25Okapi

class SearchService:
    def __init__(self):
        self.bm25_indices = {}  # document_id -> BM25 index

    def create_bm25_index(
        self,
        document_id: str,
        chunks: List[DocumentChunk]
    ):
        """Create BM25 index for keyword search"""
        tokenized_corpus = [chunk.text.split() for chunk in chunks]
        self.bm25_indices[document_id] = BM25Okapi(tokenized_corpus)

    def keyword_search(
        self,
        query: str,
        document_ids: List[str],
        top_k: int = 10
    ) -> List[SearchResult]:
        """BM25 keyword search"""
        tokenized_query = query.split()
        results = []

        for doc_id in document_ids:
            if doc_id in self.bm25_indices:
                scores = self.bm25_indices[doc_id].get_scores(tokenized_query)
                top_indices = np.argsort(scores)[-top_k:][::-1]
                results.extend(self._format_results(doc_id, scores, top_indices))

        return sorted(results, key=lambda x: x.score, reverse=True)[:top_k]

    def hybrid_search(
        self,
        semantic_results: List[SearchResult],
        keyword_results: List[SearchResult],
        alpha: float = 0.5
    ) -> List[SearchResult]:
        """Fuse semantic and keyword search results"""
        # Reciprocal Rank Fusion (RRF)
        k = 60
        scores = {}

        for rank, result in enumerate(semantic_results):
            scores[result.chunk_id] = scores.get(result.chunk_id, 0) + \
                alpha / (k + rank + 1)

        for rank, result in enumerate(keyword_results):
            scores[result.chunk_id] = scores.get(result.chunk_id, 0) + \
                (1 - alpha) / (k + rank + 1)

        # Sort by fused score
        fused = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [self._get_result(chunk_id) for chunk_id, _ in fused]
```

### 4.6 Chat Service (`chat_service.py`)

**Responsibilities:**
- Conversation management
- Chat history
- Context window management
- Memory strategies

**Class Structure:**
```python
from langchain.memory import (
    ConversationBufferMemory,
    ConversationSummaryMemory,
    ConversationBufferWindowMemory
)

class ChatService:
    def __init__(
        self,
        db: Database,
        llm_service: LLMService
    ):
        self.db = db
        self.llm_service = llm_service
        self.memories = {}  # session_id -> memory

    async def create_session(
        self,
        user_id: str,
        document_ids: List[str],
        config: ChatConfig
    ) -> ChatSession:
        """Create new chat session"""
        session = ChatSession(
            user_id=user_id,
            document_ids=document_ids,
            config=config
        )
        await self.db.save(session)

        # Initialize memory
        self.memories[session.id] = self._create_memory(config.memory_type)

        return session

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict] = None
    ) -> ChatMessage:
        """Add message to chat history"""
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            metadata=metadata
        )
        await self.db.save(message)

        # Update memory
        memory = self.memories.get(session_id)
        if memory:
            if role == "user":
                memory.chat_memory.add_user_message(content)
            elif role == "assistant":
                memory.chat_memory.add_ai_message(content)

        return message

    async def get_history(
        self,
        session_id: str,
        limit: int = 50
    ) -> List[ChatMessage]:
        """Get chat history"""
        return await self.db.get_messages(session_id, limit=limit)

    def _create_memory(
        self,
        memory_type: str
    ) -> BaseMemory:
        """Create appropriate memory type"""
        if memory_type == "buffer":
            return ConversationBufferMemory()
        elif memory_type == "window":
            return ConversationBufferWindowMemory(k=5)
        elif memory_type == "summary":
            return ConversationSummaryMemory(llm=self.llm_service)
        else:
            return ConversationBufferMemory()
```

---

## 5. Class Diagrams

### 5.1 Core Classes

```
┌─────────────────────────────────────────────────────────────────┐
│                        FlaskApp                                  │
├─────────────────────────────────────────────────────────────────┤
│ - config: Config                                                 │
│ - db: Database                                                   │
│ - services: Dict[str, Service]                                   │
├─────────────────────────────────────────────────────────────────┤
│ + create_app() -> Flask                                          │
│ + register_blueprints()                                          │
│ + init_services()                                                │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                     DocumentService                              │
├─────────────────────────────────────────────────────────────────┤
│ - config: Config                                                 │
│ - extractors: Dict[str, Extractor]                               │
│ - chunker: TextSplitter                                          │
├─────────────────────────────────────────────────────────────────┤
│ + upload_document(file, user_id) -> Document                    │
│ + extract_text(file_path, file_type) -> str                     │
│ + chunk_text(text, strategy) -> List[Chunk]                     │
│ + delete_document(document_id) -> bool                           │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                       RAGService                                 │
├─────────────────────────────────────────────────────────────────┤
│ - vector_service: VectorService                                  │
│ - search_service: SearchService                                  │
│ - llm_service: LLMService                                        │
│ - reranker: CrossEncoder                                         │
├─────────────────────────────────────────────────────────────────┤
│ + query(question, docs, config) -> QueryResult                   │
│ - _generate_queries(question) -> List[str]                       │
│ - _hybrid_search(queries, docs) -> List[Result]                  │
│ - _rerank(question, results) -> List[Result]                     │
│ - _compress_context(question, results) -> List[Result]           │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                       LLMService                                 │
├─────────────────────────────────────────────────────────────────┤
│ - providers: Dict[str, BaseProvider]                             │
│ - config: Config                                                 │
├─────────────────────────────────────────────────────────────────┤
│ + generate(prompt, model, stream) -> str | AsyncGen             │
│ + chat(messages, model, stream) -> ChatResponse                  │
│ - _get_provider(model) -> BaseProvider                           │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                     BaseProvider (Abstract)                      │
├─────────────────────────────────────────────────────────────────┤
│ + generate(prompt, model, **kwargs) -> str                       │
│ + generate_stream(prompt, model, **kwargs) -> AsyncGen          │
│ + calculate_cost(tokens, model) -> float                         │
└─────────────────────────────────────────────────────────────────┘
                                 ▲
                ┌────────────────┼────────────────┐
                │                │                │
     ┌──────────┴──────┐ ┌──────┴──────┐ ┌──────┴──────┐
     │ OpenAIProvider  │ │OllamaProvider│ │  HFProvider │
     └─────────────────┘ └──────────────┘ └─────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                     VectorService                                │
├─────────────────────────────────────────────────────────────────┤
│ - embedding_service: EmbeddingService                            │
│ - stores: Dict[str, VectorStore]                                 │
│ - config: VectorConfig                                           │
├─────────────────────────────────────────────────────────────────┤
│ + create_index(doc_id, chunks, model) -> VectorIndex            │
│ + similarity_search(query, docs, top_k) -> List[Result]         │
│ + delete_index(doc_id) -> bool                                   │
│ - _load_index(doc_id) -> VectorStore                             │
│ - _persist_index(doc_id, index) -> str                           │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Data Models

```python
# Pydantic Models for API

class DocumentUploadRequest(BaseModel):
    file: UploadFile
    metadata: Optional[Dict[str, Any]] = None

class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    file_size: int
    status: str
    num_chunks: Optional[int]
    created_at: datetime

class QueryRequest(BaseModel):
    session_id: str
    query: str
    stream: bool = False
    config: Optional[QueryConfig] = None

class QueryConfig(BaseModel):
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    max_tokens: int = 500
    top_k: int = 5
    use_reranking: bool = True
    use_compression: bool = False

class QueryResponse(BaseModel):
    message_id: str
    answer: str
    sources: List[Source]
    metadata: QueryMetadata

class Source(BaseModel):
    document_id: str
    document_name: str
    page: Optional[int]
    chunk_text: str
    score: float

class QueryMetadata(BaseModel):
    model: str
    tokens_used: int
    cost: float
    latency_ms: int
```

---

## 6. Sequence Diagrams

### 6.1 Document Upload & Indexing

```
User -> Frontend: Upload PDF
Frontend -> API: POST /documents/upload
API -> DocumentService: upload_document(file)
DocumentService -> FileSystem: Save file
DocumentService -> Extractor: extract_text(file)
Extractor -> DocumentService: Return text
DocumentService -> TextSplitter: chunk_text(text)
TextSplitter -> DocumentService: Return chunks
DocumentService -> Database: Save document metadata
DocumentService -> VectorService: create_index(chunks)
VectorService -> EmbeddingService: embed_batch(chunks)
EmbeddingService -> OpenAI: Generate embeddings
OpenAI -> EmbeddingService: Return embeddings
EmbeddingService -> VectorService: Return embeddings
VectorService -> FAISS: Create index
VectorService -> FileSystem: Persist index
VectorService -> Database: Save index metadata
VectorService -> DocumentService: Return index_id
DocumentService -> API: Return document
API -> Frontend: Return 202 (Processing)
Frontend -> User: Show success + progress
```

### 6.2 Question Answering Flow

```
User -> Frontend: Ask "What are the main findings?"
Frontend -> API: POST /chat/query
API -> ChatService: get_history(session_id)
ChatService -> Database: Fetch messages
Database -> ChatService: Return messages
ChatService -> API: Return history
API -> RAGService: query(question, docs, config)

RAGService -> LLMService: generate_queries(question)
LLMService -> RAGService: Return [query1, query2, query3]

RAGService -> VectorService: semantic_search(queries)
VectorService -> FAISS: similarity_search()
FAISS -> VectorService: Return vectors
VectorService -> RAGService: Return semantic_results

RAGService -> SearchService: keyword_search(queries)
SearchService -> BM25: search()
BM25 -> SearchService: Return results
SearchService -> RAGService: Return keyword_results

RAGService -> SearchService: hybrid_search(semantic, keyword)
SearchService -> RAGService: Return fused_results

RAGService -> CrossEncoder: rerank(question, results)
CrossEncoder -> RAGService: Return reranked_results

RAGService -> LLMService: generate(prompt, context)
LLMService -> OpenAI/Ollama: Stream response
OpenAI/Ollama -> LLMService: Stream tokens
LLMService -> RAGService: Stream answer
RAGService -> API: Stream answer + sources

API -> ChatService: save_message(answer)
ChatService -> Database: Save message
API -> Frontend: Stream response (SSE)
Frontend -> User: Display streaming answer
```

### 6.3 Local LLM Query

```
User -> Frontend: Select "Llama 3 8B"
Frontend -> API: GET /models/available
API -> LLMService: list_models()
LLMService -> OllamaProvider: check_availability()
OllamaProvider -> Ollama: GET /api/tags
Ollama -> OllamaProvider: Return models
OllamaProvider -> LLMService: Return [llama3:8b, mistral:7b]
LLMService -> API: Return models
API -> Frontend: Return available models

User -> Frontend: Ask question
Frontend -> API: POST /chat/query {model: "llama3:8b"}
API -> RAGService: query(question, model="llama3:8b")
RAGService -> [Retrieval Pipeline]: Execute
RAGService -> LLMService: generate(prompt, "llama3:8b", stream=true)
LLMService -> OllamaProvider: generate_stream()
OllamaProvider -> Ollama: POST /api/generate (stream)
Ollama -> OllamaProvider: Stream tokens
OllamaProvider -> LLMService: Stream tokens
LLMService -> RAGService: Stream tokens
RAGService -> API: Stream response
API -> Frontend: SSE stream
Frontend -> User: Display streaming response
```

---

## 7. Configuration Management

### 7.1 Environment Variables (`.env`)

```bash
# Application
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your-secret-key-here
API_VERSION=v1

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/chatpdf
# Or for SQLite: sqlite:///data/databases/chatpdf.db

# Redis
REDIS_URL=redis://localhost:6379/0

# OpenAI
OPENAI_API_KEY=sk-your-key-here
OPENAI_ORG_ID=org-your-org-id

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TIMEOUT=120

# HuggingFace
HF_API_KEY=hf_your_key_here
HF_CACHE_DIR=/data/models/huggingface

# File Storage
UPLOAD_FOLDER=/data/uploads
MAX_FILE_SIZE=50  # MB
ALLOWED_EXTENSIONS=pdf,docx,txt,md

# Vector Store
VECTOR_STORE_TYPE=faiss  # faiss or chromadb
VECTOR_STORE_PATH=/data/vector_stores
EMBEDDING_MODEL=text-embedding-ada-002
EMBEDDING_DIMENSION=1536

# RAG Configuration
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
TOP_K_RETRIEVAL=10
USE_RERANKING=True
USE_COMPRESSION=False

# LLM Defaults
DEFAULT_MODEL=gpt-3.5-turbo
DEFAULT_TEMPERATURE=0.7
DEFAULT_MAX_TOKENS=500

# Logging
LOG_LEVEL=INFO
LOG_FILE=/logs/app.log
LOG_MAX_BYTES=10485760  # 10MB
LOG_BACKUP_COUNT=5

# Security
JWT_SECRET_KEY=your-jwt-secret
JWT_ACCESS_TOKEN_EXPIRES=3600  # 1 hour
JWT_REFRESH_TOKEN_EXPIRES=2592000  # 30 days
RATE_LIMIT=100  # requests per minute

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### 7.2 Configuration Classes (`config.py`)

```python
from pydantic import BaseSettings, Field
from typing import List, Optional
import os

class Settings(BaseSettings):
    # Application
    FLASK_ENV: str = "development"
    FLASK_DEBUG: bool = True
    SECRET_KEY: str
    API_VERSION: str = "v1"

    # Database
    DATABASE_URL: str

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_ORG_ID: Optional[str] = None

    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_TIMEOUT: int = 120

    # File Storage
    UPLOAD_FOLDER: str = "./data/uploads"
    MAX_FILE_SIZE: int = 50
    ALLOWED_EXTENSIONS: List[str] = ["pdf", "docx", "txt", "md"]

    # Vector Store
    VECTOR_STORE_TYPE: str = "faiss"
    VECTOR_STORE_PATH: str = "./data/vector_stores"
    EMBEDDING_MODEL: str = "text-embedding-ada-002"
    EMBEDDING_DIMENSION: int = 1536

    # RAG
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    TOP_K_RETRIEVAL: int = 10
    USE_RERANKING: bool = True

    # LLM
    DEFAULT_MODEL: str = "gpt-3.5-turbo"
    DEFAULT_TEMPERATURE: float = 0.7
    DEFAULT_MAX_TOKENS: int = 500

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app.log"

    # Security
    JWT_SECRET_KEY: str
    JWT_ACCESS_TOKEN_EXPIRES: int = 3600
    RATE_LIMIT: int = 100

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173"]

    class Config:
        env_file = ".env"
        case_sensitive = True

# Singleton instance
settings = Settings()
```

---

## 8. Error Handling

### 8.1 Custom Exceptions

```python
class ChatPDFException(Exception):
    """Base exception for all chatPDF errors"""
    def __init__(self, message: str, code: str, status_code: int = 500):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(self.message)

class DocumentNotFoundException(ChatPDFException):
    def __init__(self, document_id: str):
        super().__init__(
            message=f"Document {document_id} not found",
            code="DOCUMENT_NOT_FOUND",
            status_code=404
        )

class DocumentProcessingException(ChatPDFException):
    def __init__(self, message: str):
        super().__init__(
            message=message,
            code="DOCUMENT_PROCESSING_ERROR",
            status_code=422
        )

class LLMProviderException(ChatPDFException):
    def __init__(self, provider: str, message: str):
        super().__init__(
            message=f"LLM Provider {provider} error: {message}",
            code="LLM_PROVIDER_ERROR",
            status_code=502
        )

class VectorStoreException(ChatPDFException):
    def __init__(self, message: str):
        super().__init__(
            message=message,
            code="VECTOR_STORE_ERROR",
            status_code=500
        )

class ValidationException(ChatPDFException):
    def __init__(self, message: str):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=400
        )

class AuthenticationException(ChatPDFException):
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            code="AUTHENTICATION_ERROR",
            status_code=401
        )

class RateLimitException(ChatPDFException):
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(
            message=message,
            code="RATE_LIMIT_EXCEEDED",
            status_code=429
        )
```

### 8.2 Error Handler Middleware

```python
from flask import jsonify
from app.utils.logger import logger

@app.errorhandler(ChatPDFException)
def handle_chatpdf_exception(error: ChatPDFException):
    logger.error(f"{error.code}: {error.message}")
    return jsonify({
        "success": False,
        "error": {
            "code": error.code,
            "message": error.message
        }
    }), error.status_code

@app.errorhandler(404)
def handle_not_found(error):
    return jsonify({
        "success": False,
        "error": {
            "code": "NOT_FOUND",
            "message": "Resource not found"
        }
    }), 404

@app.errorhandler(500)
def handle_internal_error(error):
    logger.exception("Internal server error")
    return jsonify({
        "success": False,
        "error": {
            "code": "INTERNAL_ERROR",
            "message": "An internal error occurred"
        }
    }), 500
```

### 8.3 Response Wrapper

```python
from typing import Any, Optional

class APIResponse:
    @staticmethod
    def success(
        data: Any,
        message: Optional[str] = None,
        status_code: int = 200
    ):
        response = {
            "success": True,
            "data": data
        }
        if message:
            response["message"] = message
        return jsonify(response), status_code

    @staticmethod
    def error(
        message: str,
        code: str = "ERROR",
        status_code: int = 400
    ):
        return jsonify({
            "success": False,
            "error": {
                "code": code,
                "message": message
            }
        }), status_code
```

---

## 9. Testing Strategy

### 9.1 Test Structure

```
tests/
├── conftest.py                  # Pytest fixtures
├── test_api/
│   ├── test_auth.py
│   ├── test_documents.py
│   ├── test_chat.py
│   └── test_models.py
├── test_services/
│   ├── test_document_service.py
│   ├── test_rag_service.py
│   ├── test_llm_service.py
│   └── test_vector_service.py
├── test_utils/
│   ├── test_validators.py
│   └── test_text_processing.py
└── test_integration/
    ├── test_end_to_end.py
    └── test_performance.py
```

### 9.2 Fixtures (`conftest.py`)

```python
import pytest
from app import create_app
from app.models import db
from app.config import Settings

@pytest.fixture(scope="session")
def app():
    """Create application for testing"""
    settings = Settings(
        FLASK_ENV="testing",
        DATABASE_URL="sqlite:///:memory:",
        TESTING=True
    )
    app = create_app(settings)

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    """Test client"""
    return app.test_client()

@pytest.fixture
def auth_headers(client):
    """Authenticated headers"""
    # Create test user and login
    response = client.post('/api/v1/auth/login', json={
        "email": "test@example.com",
        "password": "testpass"
    })
    token = response.json['data']['access_token']
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def sample_pdf():
    """Sample PDF file for testing"""
    return open('tests/fixtures/sample.pdf', 'rb')
```

### 9.3 Test Examples

```python
# test_api/test_documents.py

def test_upload_document(client, auth_headers, sample_pdf):
    """Test document upload"""
    response = client.post(
        '/api/v1/documents/upload',
        data={'file': sample_pdf},
        headers=auth_headers,
        content_type='multipart/form-data'
    )

    assert response.status_code == 202
    assert response.json['success'] is True
    assert 'document_id' in response.json['data']

def test_list_documents(client, auth_headers):
    """Test listing documents"""
    response = client.get(
        '/api/v1/documents',
        headers=auth_headers
    )

    assert response.status_code == 200
    assert 'documents' in response.json['data']

# test_services/test_rag_service.py

@pytest.mark.asyncio
async def test_rag_query(rag_service, sample_document):
    """Test RAG query pipeline"""
    result = await rag_service.query(
        question="What is this document about?",
        document_ids=[sample_document.id]
    )

    assert result.answer is not None
    assert len(result.sources) > 0
    assert all(s.score > 0 for s in result.sources)

# test_integration/test_end_to_end.py

def test_full_workflow(client, auth_headers, sample_pdf):
    """Test complete workflow: upload -> query -> response"""
    # 1. Upload document
    upload_response = client.post(
        '/api/v1/documents/upload',
        data={'file': sample_pdf},
        headers=auth_headers,
        content_type='multipart/form-data'
    )
    document_id = upload_response.json['data']['document_id']

    # 2. Wait for processing (poll status)
    # ... polling logic ...

    # 3. Create chat session
    session_response = client.post(
        '/api/v1/chat/sessions',
        json={'document_ids': [document_id]},
        headers=auth_headers
    )
    session_id = session_response.json['data']['session_id']

    # 4. Query document
    query_response = client.post(
        '/api/v1/chat/query',
        json={
            'session_id': session_id,
            'query': 'Summarize this document'
        },
        headers=auth_headers
    )

    assert query_response.status_code == 200
    assert query_response.json['data']['answer'] is not None
```

---

## 10. Performance Optimizations

### 10.1 Caching Strategy

```python
from functools import lru_cache
import redis
import pickle

class CacheService:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.ttl = 3600  # 1 hour

    def get_embedding(self, text: str, model: str) -> Optional[np.ndarray]:
        """Get cached embedding"""
        key = f"embedding:{model}:{hash(text)}"
        cached = self.redis.get(key)
        if cached:
            return pickle.loads(cached)
        return None

    def set_embedding(self, text: str, model: str, embedding: np.ndarray):
        """Cache embedding"""
        key = f"embedding:{model}:{hash(text)}"
        self.redis.setex(key, self.ttl, pickle.dumps(embedding))

    def get_query_result(self, query_hash: str) -> Optional[Dict]:
        """Get cached query result"""
        key = f"query:{query_hash}"
        cached = self.redis.get(key)
        if cached:
            return pickle.loads(cached)
        return None
```

### 10.2 Batch Processing

```python
async def process_documents_batch(document_ids: List[str]):
    """Process multiple documents in parallel"""
    tasks = [process_document(doc_id) for doc_id in document_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results

async def embed_batch(texts: List[str], batch_size: int = 100):
    """Generate embeddings in batches"""
    embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        batch_embeddings = await embedding_service.embed(batch)
        embeddings.extend(batch_embeddings)
    return embeddings
```

---

## Conclusion

This Low-Level Design document provides comprehensive technical specifications for implementing the advanced chatPDF system. It includes:

- Detailed project structure
- Complete database schemas
- RESTful API specifications
- Module designs with class structures
- Sequence diagrams for key flows
- Configuration management
- Error handling strategies
- Testing approaches

**Next Steps:**
1. Review and approve this LLD
2. Set up project structure
3. Begin implementation phase-by-phase
4. Implement core services first (Document, Vector, LLM)
5. Build API layer
6. Develop frontend
7. Add testing and documentation

The design is modular, scalable, and follows best practices for production-ready systems.
