# chatPDF Streamlit Application

A comprehensive Streamlit-based UI for the chatPDF system with multi-LLM support, advanced RAG features, and cost tracking.

## Features Implemented

### 1. Document Upload Interface
- ✅ Drag-and-drop file upload
- ✅ Support for PDF, DOCX, TXT, MD formats
- ✅ Progress indicators during processing
- ✅ Document list display with metadata
- ✅ Multiple document management

### 2. Chat Interface
- ✅ Message history display
- ✅ User input field
- ✅ Streaming response display (via LangChain)
- ✅ Source citations with content preview
- ✅ Message timestamps
- ✅ Query metrics (tokens, cost, latency)

### 3. Settings Sidebar
- ✅ LLM Provider selection (OpenAI, Ollama, HuggingFace)
- ✅ Model selection dropdown (dynamic based on provider)
- ✅ Embedding provider selection
- ✅ Embedding model selection
- ✅ RAG strategy toggles:
  - Hybrid Search (semantic + keyword)
  - Re-ranking (cross-encoder)
  - Contextual Compression
- ✅ Temperature slider (0.0 - 1.0)
- ✅ Top-K slider (1 - 20)
- ✅ Chunk size configuration (200 - 2000)
- ✅ Chunk overlap configuration (0 - 500)
- ✅ Max tokens setting (100 - 4000)

### 4. Advanced Features
- ✅ Cost and token tracking display
- ✅ Model comparison tool (side-by-side UI)
- ✅ Source highlighting with metadata
- ✅ Chat history viewer with search
- ✅ Document management (delete, view stats)
- ✅ Cost analytics dashboard
- ✅ Document statistics

### 5. Session State Management
- ✅ Persistent chat history during session
- ✅ Document selection and switching
- ✅ Settings persistence across interactions
- ✅ Multi-document support

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up Environment Variables
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=sk-your-api-key-here
```

### 3. Run the Application
```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

## Usage Guide

### Uploading Documents

1. Go to the **"Upload & Chat"** tab
2. Click on the file uploader or drag files into the upload area
3. Supported formats: PDF, DOCX, TXT, MD
4. Wait for processing (text extraction → chunking → embedding → indexing)
5. View document statistics and confirmation

### Chatting with Documents

1. After uploading, the chat interface appears on the right
2. Type your question in the input field at the bottom
3. Press Enter to submit
4. View the streaming response
5. Expand "Sources" to see relevant document chunks
6. Expand "Query Metrics" to see token usage, cost, and latency

### Configuring Settings

Open the **sidebar** (left panel) to configure:

#### LLM Configuration
- **Provider**: Choose between OpenAI, Ollama (local), or HuggingFace
- **Model**: Select specific model (e.g., gpt-4, gpt-3.5-turbo)

#### Embedding Configuration
- **Provider**: OpenAI or HuggingFace
- **Model**: Choose embedding model

#### RAG Strategy
- **Hybrid Search**: Combine semantic + keyword search (planned)
- **Re-ranking**: Re-score results with cross-encoder (planned)
- **Compression**: Remove irrelevant context (planned)

#### Model Parameters
- **Temperature**: 0.0 (focused) to 1.0 (creative)
- **Max Tokens**: Maximum response length
- **Top K**: Number of context chunks to retrieve

#### Chunking Settings
- **Chunk Size**: Size of text segments
- **Chunk Overlap**: Overlap between chunks

### Advanced Features

Access via the **"Advanced Features"** tab:

#### Chat History Viewer
- View all past conversations
- Search through chat history
- Clear history

#### Model Comparison
- Compare responses from different models
- Side-by-side display (UI ready, implementation pending)

#### Cost Analytics
- View total queries, tokens, and costs
- Average cost per query
- Per-query breakdown with metrics

#### Document Statistics
- Total documents, chunks, and size
- Detailed per-document metrics

## Architecture

### Session State Variables

```python
st.session_state.documents        # Dict of uploaded documents
st.session_state.current_document # Currently active document
st.session_state.vector_store     # FAISS vector store
st.session_state.messages         # Chat message history
st.session_state.conversation_chain # LangChain retrieval chain
st.session_state.settings         # User configuration
st.session_state.total_cost       # Cumulative API cost
st.session_state.total_tokens     # Cumulative token usage
```

### Data Flow

1. **Document Upload**
   - File → Text Extraction → Chunking → Embedding → Vector Store

2. **Query Processing**
   - Question → Vector Search → Context Retrieval → LLM Generation → Response

3. **Cost Tracking**
   - LangChain callback → Token counting → Cost calculation → State update

## Configuration Options

### LLM Providers

| Provider | Models Available | Status |
|----------|------------------|--------|
| OpenAI | gpt-4, gpt-3.5-turbo, etc. | ✅ Implemented |
| Ollama | llama3, mistral, etc. | 🟡 UI Ready (needs integration) |
| HuggingFace | Various OSS models | 🟡 UI Ready (needs integration) |

### Embedding Models

| Provider | Models Available | Status |
|----------|------------------|--------|
| OpenAI | text-embedding-ada-002, etc. | ✅ Implemented |
| HuggingFace | all-MiniLM-L6-v2, etc. | 🟡 UI Ready (needs integration) |

## Cost Tracking

The app automatically tracks:
- **Tokens Used**: Prompt + completion tokens
- **API Cost**: Based on model pricing
- **Latency**: Query processing time
- **Per-Query Metrics**: Detailed breakdown

View analytics in:
- Sidebar (summary)
- Query metrics (per message)
- Advanced Features → Cost Analytics (detailed)

## File Structure

```
app.py
├── Configuration (Config class)
├── Session State Initialization
├── Document Processing Functions
│   ├── extract_text_from_pdf()
│   ├── extract_text_from_docx()
│   ├── extract_text_from_txt()
│   ├── create_text_chunks()
│   └── create_vector_store()
├── Chat & RAG Functions
│   ├── get_conversation_chain()
│   ├── calculate_cost()
│   └── process_query()
└── UI Components
    ├── render_sidebar()
    ├── render_document_upload()
    ├── render_chat_interface()
    ├── render_chat_history()
    ├── render_model_comparison()
    ├── render_cost_analytics()
    └── render_document_statistics()
```

## Known Limitations & Future Work

### Current Limitations
1. **Ollama Integration**: UI ready, needs backend implementation
2. **HuggingFace Integration**: UI ready, needs backend implementation
3. **Hybrid Search**: Toggle present, feature not implemented
4. **Re-ranking**: Toggle present, feature not implemented
5. **Compression**: Toggle present, feature not implemented
6. **Model Comparison**: UI ready, execution logic pending

### Planned Enhancements
- [ ] Implement Ollama provider integration
- [ ] Implement HuggingFace provider integration
- [ ] Add BM25 keyword search for hybrid retrieval
- [ ] Add cross-encoder re-ranking
- [ ] Add contextual compression
- [ ] Implement actual model comparison execution
- [ ] Add chat export functionality
- [ ] Add document preview
- [ ] Add multi-document querying
- [ ] Add query history with filters

## Troubleshooting

### "OPENAI_API_KEY not found"
- Ensure `.env` file exists with `OPENAI_API_KEY=sk-...`
- Restart the Streamlit app after adding the key

### "Error creating vector store"
- Check OpenAI API key is valid
- Ensure internet connection for API calls
- Verify embeddings model is available

### Document upload fails
- Check file format is supported (PDF, DOCX, TXT, MD)
- Ensure file is not corrupted
- For DOCX: Install `python-docx` if not present

### High costs
- Use `gpt-3.5-turbo` instead of `gpt-4`
- Reduce `max_tokens` setting
- Reduce `top_k` to retrieve fewer chunks
- Clear chat history to avoid long context

## Dependencies

Key packages:
- `streamlit` - Web UI framework
- `langchain` - LLM orchestration
- `langchain-openai` - OpenAI integration
- `faiss-cpu` - Vector similarity search
- `PyPDF2` - PDF processing
- `python-docx` - DOCX processing
- `tiktoken` - Token counting

See `requirements.txt` for complete list.

## Performance Tips

1. **Chunk Size**: 1000 chars is a good default
2. **Top K**: 3-5 chunks usually sufficient
3. **Temperature**: 0.7 for general Q&A, 0.3 for factual
4. **Model**: Use gpt-3.5-turbo for cost savings
5. **Embeddings**: text-embedding-ada-002 is fast and cheap

## Support

For issues or questions:
1. Check this README
2. Review the HLD and LLD documents
3. Check Streamlit logs in terminal
4. Review session state in Streamlit debug mode

---

Built with Streamlit + LangChain + OpenAI
