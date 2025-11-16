# High-Level Design (HLD) - Advanced chatPDF System

## 1. System Overview

### 1.1 Purpose
Transform the basic chatPDF application into an enterprise-grade document question-answering system with:
- Advanced RAG (Retrieval-Augmented Generation) capabilities
- Multi-LLM support (Cloud & Local models)
- Modern web interface
- RESTful API backend
- Multi-user support with session management
- Production-ready deployment

### 1.2 Key Features
- **Multi-format Document Support**: PDF, DOCX, TXT, Markdown, HTML
- **Advanced RAG Pipeline**: Hybrid search, re-ranking, multi-query retrieval
- **Local & Cloud LLMs**: OpenAI, Ollama, HuggingFace, LlamaCPP
- **Conversational Memory**: Context-aware multi-turn conversations
- **Document Management**: Upload, delete, organize documents
- **Source Attribution**: Citations with page/paragraph references
- **Cost Tracking**: Monitor API usage and costs
- **Multi-user Support**: User sessions and document isolation
- **Real-time Streaming**: Stream responses for better UX

---

## 2. System Architecture

### 2.1 Architecture Diagram
```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                             │
│  ┌──────────────────┐              ┌──────────────────┐         │
│  │   React Frontend │              │  Streamlit UI    │         │
│  │   (TypeScript)   │              │  (Alternative)   │         │
│  └──────────────────┘              └──────────────────┘         │
└────────────────┬──────────────────────────┬─────────────────────┘
                 │                          │
                 │     REST API (HTTP/WS)   │
                 │                          │
┌────────────────┴──────────────────────────┴─────────────────────┐
│                      API GATEWAY LAYER                           │
│  ┌────────────────────────────────────────────────────────┐     │
│  │              Flask Application (Backend)                │     │
│  │  - Authentication & Authorization                       │     │
│  │  - Request Validation                                   │     │
│  │  - Rate Limiting                                        │     │
│  │  - CORS Handling                                        │     │
│  └────────────────────────────────────────────────────────┘     │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────┴──────────────────────────────────┐
│                      SERVICE LAYER                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Document   │  │     RAG      │  │     LLM      │          │
│  │   Service    │  │   Service    │  │   Service    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Vector     │  │    Chat      │  │   Embedding  │          │
│  │   Service    │  │   Service    │  │   Service    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────┴──────────────────────────────────┐
│                      DATA LAYER                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  PostgreSQL  │  │    FAISS     │  │   ChromaDB   │          │
│  │  (Metadata)  │  │  (Vectors)   │  │  (Optional)  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │    Redis     │  │  File System │  │    S3/Blob   │          │
│  │   (Cache)    │  │  (Documents) │  │  (Optional)  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                      EXTERNAL SERVICES                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   OpenAI     │  │    Ollama    │  │ HuggingFace  │          │
│  │     API      │  │   (Local)    │  │     API      │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└──────────────────────────────────────────────────────────────────┘
```

### 2.2 Component Responsibilities

#### 2.2.1 Frontend Layer
- **React Application**:
  - Modern, responsive UI with TypeScript
  - Document upload with drag-n-drop
  - Chat interface with streaming responses
  - Document viewer with source highlighting
  - Settings panel for LLM/RAG configuration
  - Analytics dashboard

- **Streamlit Alternative**:
  - Quick prototyping and demos
  - Simpler deployment option
  - Less customization

#### 2.2.2 API Gateway (Flask Backend)
- **Core Responsibilities**:
  - HTTP request routing
  - WebSocket for streaming
  - Input validation & sanitization
  - Authentication (JWT tokens)
  - Session management
  - Error handling & logging
  - Rate limiting & throttling
  - API documentation (Swagger/OpenAPI)

#### 2.2.3 Service Layer

**Document Service**:
- Document upload/download/delete
- Format detection and validation
- Text extraction (PDF, DOCX, TXT, etc.)
- Document preprocessing
- Metadata extraction
- Document versioning

**RAG Service**:
- Advanced retrieval strategies
- Hybrid search (semantic + keyword)
- Multi-query retrieval
- Contextual compression
- Re-ranking with cross-encoders
- Source attribution

**LLM Service**:
- Multi-provider support (OpenAI, Ollama, HF)
- Model selection and routing
- Prompt engineering
- Response streaming
- Fallback mechanisms
- Cost tracking

**Vector Service**:
- Embedding generation
- Vector store management (FAISS/ChromaDB)
- Similarity search
- Index optimization
- Batch processing

**Chat Service**:
- Conversation management
- Chat history storage
- Context window management
- Multi-turn dialogue handling
- Memory strategies (buffer, summary, knowledge graph)

**Embedding Service**:
- Multiple embedding models
- OpenAI embeddings
- HuggingFace embeddings
- Local embeddings (all-MiniLM, BGE, etc.)
- Embedding caching

#### 2.2.4 Data Layer

**PostgreSQL**:
- User accounts
- Document metadata
- Chat history
- Session data
- Usage analytics
- System configuration

**Vector Stores**:
- FAISS: Fast similarity search
- ChromaDB: Alternative with built-in persistence
- Index persistence and loading

**Redis**:
- Session caching
- Rate limiting counters
- Temporary embeddings cache
- Real-time analytics

**File System / Object Storage**:
- Document storage (local or S3-compatible)
- Vector index files
- Model cache
- Logs

---

## 3. Technology Stack

### 3.1 Backend
| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Web Framework** | Flask 3.0+ | REST API, lightweight, flexible |
| **WSGI Server** | Gunicorn | Production server |
| **Database** | PostgreSQL 15+ | Relational data storage |
| **ORM** | SQLAlchemy 2.0+ | Database abstraction |
| **Cache** | Redis 7+ | Session & data caching |
| **Task Queue** | Celery (optional) | Async document processing |
| **Validation** | Pydantic | Request/response validation |

### 3.2 AI/ML Stack
| Component | Technology | Purpose |
|-----------|-----------|---------|
| **LLM Framework** | LangChain 0.3+ | RAG orchestration |
| **Cloud LLM** | OpenAI GPT-4/3.5 | High-quality responses |
| **Local LLM** | Ollama (Llama 3, Mistral) | Privacy, cost savings |
| **Embeddings** | OpenAI, HuggingFace, Local | Semantic search |
| **Vector Store** | FAISS, ChromaDB | Similarity search |
| **Re-ranker** | Cross-encoders (HF) | Result refinement |

### 3.3 Frontend
| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Framework** | React 18+ | Modern UI |
| **Language** | TypeScript | Type safety |
| **Build Tool** | Vite | Fast development |
| **Styling** | Tailwind CSS | Utility-first CSS |
| **State Management** | Zustand/Redux | Global state |
| **HTTP Client** | Axios | API communication |
| **Alternative** | Streamlit 1.35+ | Rapid prototyping |

### 3.4 DevOps
| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Containerization** | Docker | Consistent environments |
| **Orchestration** | Docker Compose | Multi-container setup |
| **CI/CD** | GitHub Actions | Automated testing/deployment |
| **Monitoring** | Prometheus + Grafana | Performance monitoring |
| **Logging** | Python logging + ELK stack | Centralized logging |

---

## 4. Data Flow

### 4.1 Document Upload & Indexing Flow
```
User uploads document
        ↓
Frontend validates file (type, size)
        ↓
POST /api/documents/upload
        ↓
Flask API validates & saves file
        ↓
Extract text (PyPDF2, docx, etc.)
        ↓
Chunk text (RecursiveCharacterTextSplitter)
        ↓
Generate embeddings (OpenAI/Local)
        ↓
Store in vector database (FAISS/ChromaDB)
        ↓
Save metadata to PostgreSQL
        ↓
Return document_id to client
```

### 4.2 Question Answering Flow
```
User asks question
        ↓
POST /api/chat/query
        ↓
Load conversation history (PostgreSQL)
        ↓
Generate search queries (multi-query)
        ↓
Hybrid search:
  - Semantic search (vector similarity)
  - Keyword search (BM25)
        ↓
Merge and deduplicate results
        ↓
Re-rank with cross-encoder
        ↓
Contextual compression
        ↓
Build prompt with context
        ↓
Call LLM (streaming)
        ↓
Extract source citations
        ↓
Save to chat history
        ↓
Stream response to client (WebSocket/SSE)
```

### 4.3 Local LLM Query Flow
```
User selects local model (Ollama)
        ↓
Check if Ollama is running
        ↓
If not: Show installation instructions
        ↓
If yes: List available models
        ↓
User selects model (llama3, mistral, etc.)
        ↓
Send query to Ollama API (localhost:11434)
        ↓
Stream response back to user
```

---

## 5. Key Design Decisions

### 5.1 Why Flask over FastAPI?
- **Pros**: Mature ecosystem, simpler learning curve, extensive documentation
- **Cons**: FastAPI has native async support
- **Decision**: Flask with proper structure; can migrate to FastAPI later if needed

### 5.2 Vector Store: FAISS vs ChromaDB
- **FAISS**:
  - Pros: Extremely fast, battle-tested, Facebook-backed
  - Cons: Requires manual persistence
- **ChromaDB**:
  - Pros: Built-in persistence, easier to use, metadata filtering
  - Cons: Slightly slower
- **Decision**: Support both, default to FAISS for speed

### 5.3 Local LLM Strategy
- **Primary**: Ollama (easiest setup, good performance)
- **Secondary**: LlamaCPP (more control, GGUF support)
- **Tertiary**: HuggingFace Transformers (most flexible)
- **Decision**: Implement Ollama first, add others as plugins

### 5.4 Frontend: React vs Streamlit
- **React**: Production-grade, full control, better UX
- **Streamlit**: Faster development, easier maintenance
- **Decision**: Build both, React as primary, Streamlit as alternative

### 5.5 Database Choice
- **SQLite**: Good for development, single-file
- **PostgreSQL**: Production-ready, better concurrency
- **Decision**: SQLite for dev, PostgreSQL for production

---

## 6. Advanced RAG Features

### 6.1 Hybrid Search
Combine multiple retrieval strategies:
1. **Semantic Search**: Vector similarity (FAISS)
2. **Keyword Search**: BM25/TF-IDF for exact matches
3. **Metadata Filtering**: Filter by document, date, type
4. **Weighted Fusion**: Combine scores with configurable weights

### 6.2 Multi-Query Retrieval
Generate multiple search queries from user question:
- Original query
- Rephrased queries (2-3 variations)
- Decomposed sub-queries
- Retrieve for each, merge results

### 6.3 Re-ranking
Two-stage retrieval:
1. **First stage**: Fast retrieval (100-200 chunks)
2. **Second stage**: Re-rank with cross-encoder (top 10-20)
3. Models: `cross-encoder/ms-marco-MiniLM-L-12-v2`

### 6.4 Contextual Compression
- Remove irrelevant sentences from retrieved chunks
- Extract only relevant portions
- Reduce token usage
- Improve answer quality

### 6.5 Source Attribution
Track and return:
- Document name and page number
- Exact text snippet used
- Confidence score
- Link to original document

---

## 7. Security Considerations

### 7.1 Authentication & Authorization
- JWT-based authentication
- Role-based access control (RBAC)
- API key management for services
- Session timeout and refresh

### 7.2 Data Security
- File upload validation (type, size, content)
- Sanitize file names and content
- Encrypt sensitive data at rest
- Use environment variables for secrets
- Rate limiting per user/IP

### 7.3 API Security
- CORS configuration
- Input validation and sanitization
- SQL injection prevention (ORM)
- XSS protection
- CSRF tokens for state-changing operations

---

## 8. Scalability Considerations

### 8.1 Horizontal Scaling
- Stateless API servers (scale with load balancer)
- Separate vector search service
- Database connection pooling
- Redis for distributed caching

### 8.2 Performance Optimization
- Lazy loading of models
- Batch embedding generation
- Vector index optimization (IVF, HNSW)
- Response caching for common queries
- CDN for static assets

### 8.3 Resource Management
- Model quantization (4-bit, 8-bit)
- GPU acceleration when available
- Memory-mapped vector indices
- Streaming for large responses

---

## 9. Deployment Architecture

### 9.1 Development Environment
```yaml
Services:
  - Flask (port 5000)
  - React Dev Server (port 5173)
  - PostgreSQL (port 5432)
  - Redis (port 6379)
  - Ollama (port 11434)
```

### 9.2 Production Environment
```yaml
Load Balancer (Nginx/Traefik)
    ↓
Flask App (Gunicorn, 4 workers)
    ↓
├── PostgreSQL (managed service)
├── Redis (managed service)
├── S3 (document storage)
└── Ollama (dedicated GPU server)
```

### 9.3 Docker Compose Setup
- Multi-stage builds for optimization
- Separate containers for each service
- Named volumes for persistence
- Health checks for all services
- Auto-restart policies

---

## 10. Monitoring & Observability

### 10.1 Metrics to Track
- Request latency (p50, p95, p99)
- Error rates by endpoint
- Token usage and costs
- Vector search performance
- Database query performance
- Cache hit rates

### 10.2 Logging Strategy
- Structured logging (JSON format)
- Log levels: DEBUG, INFO, WARNING, ERROR
- Request/response logging
- Error stack traces
- Audit logs for sensitive operations

### 10.3 Health Checks
- `/health` endpoint
- Database connectivity
- Redis connectivity
- Vector store status
- LLM service availability
- Disk space monitoring

---

## 11. Future Enhancements

### 11.1 Phase 2 Features
- Multi-modal support (images, tables in PDFs)
- Voice input/output
- Document comparison
- Automatic summarization
- Knowledge graph integration

### 11.2 Advanced Features
- Fine-tuned models for domain-specific tasks
- Active learning for improving retrieval
- Federated search across multiple sources
- Collaborative features (shared documents)
- Advanced analytics and insights

### 11.3 Enterprise Features
- SSO integration (SAML, OAuth)
- Audit logging and compliance
- Data residency controls
- Custom model deployment
- SLA monitoring and reporting

---

## 12. Migration Strategy

### 12.1 From Current System
1. Keep existing `streamlit_app.py` working
2. Build new backend in parallel
3. Migrate one feature at a time
4. Deprecate old code gradually
5. Maintain backward compatibility

### 12.2 Data Migration
- Export existing vector indices
- Re-index with new chunking strategy
- Migrate chat history format
- Update configuration format

---

## 13. Success Metrics

### 13.1 Technical Metrics
- Response time < 2s for queries
- 99.9% uptime
- Support 100+ concurrent users
- Index 1000+ documents
- < $0.01 per query (with local LLMs)

### 13.2 Quality Metrics
- Answer accuracy > 90%
- User satisfaction > 4.5/5
- Retrieval precision > 85%
- Source attribution accuracy > 95%

---

## 14. Documentation Requirements

### 14.1 User Documentation
- Installation guide
- User manual with screenshots
- API documentation (Swagger)
- Configuration guide
- Troubleshooting guide

### 14.2 Developer Documentation
- Architecture overview (this document)
- Code structure and patterns
- API reference
- Testing guidelines
- Contribution guide

---

## Conclusion

This HLD provides a comprehensive blueprint for transforming chatPDF into a production-ready, enterprise-grade document Q&A system with advanced RAG capabilities, multi-LLM support, and modern architecture. The design prioritizes:

1. **Modularity**: Easy to extend and maintain
2. **Scalability**: Handles growth in users and documents
3. **Flexibility**: Supports multiple LLMs and configurations
4. **Security**: Enterprise-grade security measures
5. **Performance**: Optimized for speed and efficiency
6. **Usability**: Modern, intuitive interface

Next step: Create the Low-Level Design (LLD) document with detailed technical specifications.
