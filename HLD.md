# High-Level Design (HLD) - Advanced chatPDF System

## 1. System Overview

### 1.1 Purpose
Transform the basic chatPDF application into an **LLM and RAG-focused** document question-answering system with:
- **Advanced RAG techniques** (Retrieval-Augmented Generation)
- **Multi-LLM support** (Cloud & Local models)
- **Simple, functional interface** (Streamlit)
- **Focus on AI/ML concepts** rather than infrastructure

### 1.2 Key Features
- **Multi-format Document Support**: PDF, DOCX, TXT, Markdown
- **Advanced RAG Pipeline**: Hybrid search, re-ranking, multi-query retrieval, contextual compression
- **Local & Cloud LLMs**: OpenAI, Ollama, HuggingFace
- **Multiple Embedding Models**: OpenAI, HuggingFace, Local embeddings
- **Conversational Memory**: Context-aware multi-turn conversations
- **Document Management**: Upload, delete, organize documents
- **Source Attribution**: Citations with page/paragraph references
- **Cost Tracking**: Monitor API usage and costs
- **Real-time Streaming**: Stream responses for better UX
- **Comparison Tools**: Compare different LLMs and RAG strategies

---

## 2. System Architecture

### 2.1 Simplified Architecture Diagram
```
┌──────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                         │
│                  ┌──────────────────┐                        │
│                  │  Streamlit UI    │                        │
│                  │  - Chat Interface │                        │
│                  │  - Doc Upload    │                        │
│                  │  - Settings      │                        │
│                  └──────────────────┘                        │
└─────────────────────────┬────────────────────────────────────┘
                          │
┌─────────────────────────┴────────────────────────────────────┐
│                 CORE SERVICE LAYER (Python)                   │
│  ┌────────────┐  ┌────────────┐  ┌─────────────┐            │
│  │  Document  │  │    RAG     │  │     LLM     │            │
│  │  Service   │  │  Service   │  │   Service   │            │
│  │            │  │  ┌──────┐  │  │ ┌─────────┐ │            │
│  │ • Extract  │  │  │Hybrid│  │  │ │ OpenAI  │ │            │
│  │ • Chunk    │  │  │Search│  │  │ │ Ollama  │ │            │
│  │ • Process  │  │  │Rerank│  │  │ │HuggingFace│           │
│  └────────────┘  │  └──────┘  │  │ └─────────┘ │            │
│                  │             │  └─────────────┘            │
│  ┌────────────┐  └─────────────┘                             │
│  │  Vector    │  ┌────────────┐  ┌─────────────┐            │
│  │  Service   │  │   Chat     │  │  Embedding  │            │
│  │            │  │  Service   │  │   Service   │            │
│  │ • Embed    │  │            │  │             │            │
│  │ • Search   │  │ • Memory   │  │ • OpenAI   │            │
│  │ • Index    │  │ • History  │  │ • HF Models│            │
│  └────────────┘  └────────────┘  └─────────────┘            │
└─────────────────────────┬────────────────────────────────────┘
                          │
┌─────────────────────────┴────────────────────────────────────┐
│                      DATA LAYER                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │    SQLite    │  │    FAISS     │  │  File System │       │
│  │  (Metadata)  │  │  (Vectors)   │  │  (Documents) │       │
│  │              │  │              │  │              │       │
│  │ • Documents  │  │ • Embeddings │  │ • PDFs       │       │
│  │ • Chat       │  │ • Indices    │  │ • DOCX       │       │
│  │ • Analytics  │  │              │  │ • TXT        │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                    EXTERNAL LLM SERVICES                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   OpenAI     │  │    Ollama    │  │ HuggingFace  │       │
│  │     API      │  │   (Local)    │  │     Hub      │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 Component Responsibilities

#### 2.2.1 Presentation Layer (Streamlit)
- **Simple, Functional UI**:
  - Document upload with drag-n-drop
  - Chat interface with streaming responses
  - Source highlighting and citations
  - Settings panel for:
    - LLM selection (OpenAI, Ollama, HuggingFace)
    - Embedding model selection
    - RAG strategy configuration (hybrid search, re-ranking, etc.)
    - Temperature, top_k, chunk size parameters
  - Side-by-side LLM comparison
  - Cost and token usage tracking
  - Chat history viewer

#### 2.2.2 Core Service Layer

**Document Service**:
- Document upload/delete
- Format detection (PDF, DOCX, TXT, MD)
- Text extraction using PyPDF2, python-docx
- Document preprocessing and cleaning
- **Chunking strategies**:
  - RecursiveCharacterTextSplitter (default)
  - SemanticChunker (split by meaning)
  - Token-based splitting
- Metadata extraction

**RAG Service** (Focus Area):
- **Hybrid Search**: Combine semantic + keyword (BM25)
- **Multi-Query Retrieval**: Generate multiple search variations
- **Re-ranking**: Cross-encoder scoring for relevance
- **Contextual Compression**: Remove irrelevant text
- **Query Decomposition**: Break complex queries into sub-queries
- **Source Attribution**: Track and cite sources
- **Configurable Strategies**: Switch between different RAG approaches

**LLM Service** (Focus Area):
- **Multi-Provider Support**:
  - OpenAI (GPT-4, GPT-3.5)
  - Ollama (Llama 3, Mistral, CodeLlama, etc.)
  - HuggingFace (any model from hub)
- **Prompt Engineering**: Templates for different tasks
- **Response Streaming**: Real-time token generation
- **Model Comparison**: Run same query on multiple models
- **Cost Tracking**: Track tokens and API costs
- **Fallback**: Auto-switch on failures

**Vector Service** (Focus Area):
- **Embedding Generation**:
  - OpenAI embeddings
  - HuggingFace models (all-MiniLM, BGE, etc.)
  - Local sentence transformers
- **Vector Stores**: FAISS for fast similarity search
- **Similarity Search**: Cosine, L2, dot product
- **Index Optimization**: IVF, HNSW for large datasets
- **Batch Processing**: Efficient bulk embedding

**Chat Service**:
- **Conversation Memory**:
  - Buffer memory (recent N messages)
  - Summary memory (LLM-generated summaries)
  - Window memory (sliding context)
- Chat history storage (SQLite)
- Context window management
- Multi-turn dialogue support

**Embedding Service** (Focus Area):
- **Compare Embedding Models**:
  - OpenAI text-embedding-ada-002
  - HuggingFace all-MiniLM-L6-v2
  - sentence-transformers/all-mpnet-base-v2
  - BAAI/bge-small-en-v1.5
- Model performance comparison
- Dimension reduction techniques
- Embedding visualization (optional)

#### 2.2.3 Data Layer

**SQLite** (Simple local database):
- Document metadata
- Chat history
- Usage analytics (tokens, cost)
- Configuration settings

**FAISS** (Vector similarity search):
- Fast similarity search
- Index persistence (saved as .index files)
- Supports large-scale vector search
- Minimal memory footprint

**File System**:
- Document storage (data/uploads/)
- Vector index files (data/vector_stores/)
- Model cache (data/models/)
- Logs (logs/)

---

## 3. Technology Stack

### 3.1 Core Python Stack
| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Framework** | Streamlit 1.35+ | Simple, functional UI |
| **Database** | SQLite 3 | Lightweight local storage |
| **ORM** | SQLAlchemy 2.0+ | Database abstraction |
| **Validation** | Pydantic | Data validation |

### 3.2 LLM & RAG Stack (Core Focus)
| Component | Technology | Purpose |
|-----------|-----------|---------|
| **LLM Framework** | LangChain 0.3+ | RAG orchestration & chains |
| **Cloud LLM** | OpenAI (GPT-4, GPT-3.5) | High-quality responses |
| **Local LLM** | Ollama (Llama 3, Mistral, etc.) | Privacy, zero-cost inference |
| **Alternative LLM** | HuggingFace Transformers | Any OSS model |
| **Embeddings** | OpenAI, sentence-transformers | Semantic representations |
| **Vector Store** | FAISS | Fast similarity search |
| **Keyword Search** | rank-bm25 | Traditional IR |
| **Re-ranker** | sentence-transformers cross-encoders | Result refinement |
| **Token Counter** | tiktoken | Accurate token counting |

### 3.3 Document Processing
| Component | Technology | Purpose |
|-----------|-----------|---------|
| **PDF** | PyPDF2 3.0+ | PDF text extraction |
| **Word Docs** | python-docx 1.1+ | DOCX processing |
| **Text Splitting** | LangChain TextSplitters | Smart chunking |
| **Text Processing** | NLTK, spaCy (optional) | Advanced NLP |

### 3.4 Development & Deployment
| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Package Manager** | pip | Dependency management |
| **Environment** | python-dotenv | Config management |
| **Testing** | pytest | Unit/integration tests |
| **Logging** | Python logging | Debug & monitoring |
| **Containerization** | Docker (optional) | Easy deployment |

---

## 4. Data Flow (Simplified)

### 4.1 Document Upload & Indexing Flow
```
User uploads document via Streamlit
        ↓
Validate file (type, size)
        ↓
Save to data/uploads/
        ↓
DocumentService: Extract text (PyPDF2, python-docx)
        ↓
DocumentService: Chunk text
  - RecursiveCharacterTextSplitter (default)
  - Or SemanticChunker
  - Or Token-based splitter
        ↓
EmbeddingService: Generate embeddings
  - User chooses: OpenAI / HuggingFace / Local
        ↓
VectorService: Create FAISS index
        ↓
VectorService: Save index to data/vector_stores/
        ↓
Save metadata to SQLite (documents table)
        ↓
Display success + document stats to user
```

### 4.2 Advanced RAG Query Flow (Core Feature)
```
User asks question in chat interface
        ↓
Load conversation history from SQLite
        ↓
RAGService: Multi-Query Generation
  - Original query
  - 2-3 rephrased variations using LLM
        ↓
RAGService: Hybrid Search
  ├─> VectorService: Semantic search (FAISS)
  │   - Embed query
  │   - Find top-K similar chunks
  └─> SearchService: Keyword search (BM25)
      - TF-IDF weighted keyword matching
        ↓
RAGService: Merge results
  - Reciprocal Rank Fusion (RRF)
  - Combine semantic + keyword scores
        ↓
RAGService: Re-ranking (if enabled)
  - Cross-encoder scores query-chunk pairs
  - Keep top 5-10 most relevant
        ↓
RAGService: Contextual Compression (if enabled)
  - Remove irrelevant sentences
  - Extract only relevant portions
        ↓
LLMService: Build prompt with context
  - System prompt + retrieved chunks + query
        ↓
LLMService: Generate answer (streaming)
  - User's selected model (OpenAI / Ollama / HF)
  - Stream tokens to UI
        ↓
Extract source citations
  - Document name, page number, relevance score
        ↓
Save message to SQLite (chat_history)
        ↓
Display streaming answer + sources to user
```

### 4.3 Local LLM with Ollama Flow
```
User selects "Ollama" provider in settings
        ↓
LLMService: Check Ollama availability
  - HTTP GET http://localhost:11434/api/tags
        ↓
If Ollama not running:
  - Display installation instructions
  - Link to ollama.ai
        ↓
If Ollama running:
  - List available models (llama3, mistral, etc.)
  - Display model info (size, params)
        ↓
User selects model and asks question
        ↓
LLMService: Send to Ollama
  - POST http://localhost:11434/api/generate
  - Stream: true
        ↓
Stream tokens to UI (zero cost!)
        ↓
Display answer with "Model: llama3:8b (local)"
```

---

## 5. Key Design Decisions

### 5.1 Why Streamlit over Flask/React?
- **Focus on LLM concepts, not web development**
- **Rapid prototyping**: Build UI in minutes
- **Built-in widgets**: File upload, sliders, selectboxes
- **Automatic re-runs**: No need for state management
- **Decision**: Streamlit for simplicity and speed

### 5.2 Why FAISS for Vector Storage?
- **Speed**: Extremely fast similarity search (Facebook-built)
- **Scalability**: Handles millions of vectors
- **No server required**: Just save/load index files
- **Lightweight**: Minimal dependencies
- **Decision**: FAISS as primary, focus on optimizing search

### 5.3 Local LLM Strategy
- **Primary**: Ollama (easiest setup, one-command install)
- **Why Ollama**:
  - Simple API (HTTP REST)
  - Auto-handles model downloads
  - Optimized inference
  - Supports most popular models
- **Secondary**: HuggingFace Transformers (more model variety)
- **Decision**: Implement Ollama first, focus on ease of use

### 5.4 Database: SQLite Only
- **Why SQLite**:
  - Zero configuration
  - Single file database
  - Perfect for local/personal use
  - Built into Python
- **No need for PostgreSQL**: Not building multi-user system
- **Decision**: SQLite for all storage needs

### 5.5 No Authentication Layer
- **Reasoning**:
  - Single-user local application
  - Focus on RAG/LLM concepts, not security
  - Simplifies architecture significantly
  - Faster development
- **Decision**: Skip auth, focus on core AI features

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

## 7. Performance Optimization (LLM-Focused)

### 7.1 LLM Optimization
- **Model Quantization**: Use 4-bit/8-bit quantized models for local LLMs
- **Streaming**: Always stream responses for better perceived performance
- **Caching**: Cache embeddings for frequently used text
- **Batch Processing**: Generate embeddings in batches

### 7.2 Vector Search Optimization
- **Index Selection**: IVF for large datasets, Flat for small
- **Dimension Reduction**: Optionally reduce embedding dimensions
- **Memory Mapping**: Use memory-mapped FAISS indices for large collections
- **Top-K Tuning**: Adjust retrieval count based on needs

### 7.3 RAG Pipeline Optimization
- **Lazy Re-ranking**: Only re-rank when needed
- **Compression**: Enable contextual compression to reduce LLM tokens
- **Parallel Search**: Run semantic + keyword search in parallel
- **Smart Chunking**: Tune chunk size/overlap for your documents

---

## 8. Simple Deployment

### 8.1 Local Development
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Install Ollama (optional, for local LLMs)
curl https://ollama.ai/install.sh | sh
ollama pull llama3

# 3. Set up environment
cp .env.example .env
# Edit .env with your OpenAI API key (if using)

# 4. Run application
streamlit run app.py
```

### 8.2 Docker Deployment (Optional)
```yaml
# docker-compose.yml
services:
  chatpdf:
    build: .
    ports:
      - "8501:8501"
    volumes:
      - ./data:/app/data
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}

  ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama:/root/.ollama
```

---

## 9. Logging & Monitoring (Simple)

### 9.1 Key Metrics to Track
- **Token usage and API costs** (per query)
- **Query latency** (document processing, embedding, LLM generation)
- **Retrieval quality** (relevance scores, sources found)
- **Model comparison** (accuracy, cost, speed)

### 9.2 Simple Logging
- **Python logging** to file and console
- **Log Levels**: INFO for queries, DEBUG for detailed RAG steps
- **Cost Tracking**: Log every OpenAI API call with tokens/cost
- **Error Handling**: Graceful fallbacks for missing models/services

---

## 10. Future LLM/RAG Enhancements

### 10.1 Advanced RAG Techniques
- **Parent Document Retrieval**: Retrieve small chunks, return larger context
- **Hypothetical Document Embeddings (HyDE)**: Generate hypothetical answers, search with them
- **Query Routing**: Route different query types to specialized retrievers
- **Self-Querying**: Extract filters from natural language queries
- **Ensemble Retrievers**: Combine multiple retrieval strategies

### 10.2 Multi-Modal RAG
- **Image Extraction**: Extract and describe images from PDFs
- **Table Understanding**: Parse and query tables
- **Document Layout**: Use visual structure for better chunking
- **Vision-Language Models**: Use models like GPT-4V, LLaVA

### 10.3 Advanced LLM Features
- **Fine-Tuning**: Fine-tune local models on your documents
- **Prompt Optimization**: A/B test different prompts
- **Agent Workflows**: Multi-step reasoning with LangChain agents
- **Tool Use**: Let LLM call functions (calculators, search, etc.)
- **Mixture of Models**: Route different tasks to specialized models

### 10.4 Evaluation & Experimentation
- **RAG Evaluation**: Implement RAGAS, TruLens for quality metrics
- **A/B Testing**: Compare different RAG strategies
- **Ground Truth**: Build test sets with questions/answers
- **Embedding Comparison**: Benchmark different embedding models
- **LLM Leaderboard**: Track which models work best for your use case

---

## 11. Learning Objectives

This project is designed to teach key LLM concepts:

### 11.1 Embeddings
- How text becomes numbers
- Semantic vs syntactic similarity
- Embedding model selection
- Dimensionality and performance tradeoffs

### 11.2 Vector Databases
- Similarity search algorithms
- Index types (Flat, IVF, HNSW)
- Approximate vs exact search
- Scaling to millions of vectors

### 11.3 RAG Patterns
- Naive RAG vs Advanced RAG
- Retrieval strategies
- Context optimization
- Handling multi-turn conversations

### 11.4 LLM Integration
- API vs local models
- Streaming responses
- Cost optimization
- Prompt engineering
- Context window management

### 11.5 Production Considerations
- Latency optimization
- Cost tracking
- Error handling
- Model versioning

---

## Conclusion

This HLD provides a blueprint for transforming chatPDF into an **LLM and RAG-focused** document Q&A system. The design prioritizes:

1. **Learning Focus**: Understand embeddings, vector search, RAG patterns, and LLM integration
2. **Simplicity**: Streamlit UI, SQLite database, local files - no complex infrastructure
3. **Flexibility**: Support multiple LLMs (OpenAI, Ollama, HuggingFace) and embeddings
4. **Advanced RAG**: Hybrid search, re-ranking, multi-query, contextual compression
5. **Cost Optimization**: Local LLMs with Ollama for zero-cost inference
6. **Experimentation**: Compare models, strategies, and configurations

**Core Philosophy**:
- Focus on AI/ML concepts, not web development
- Keep it simple and educational
- Make it easy to experiment and learn
- Prioritize functionality over polish

Next step: Simplify the Low-Level Design (LLD) document with streamlined technical specifications focused on RAG and LLM components.
