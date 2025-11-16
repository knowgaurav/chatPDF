# chatPDF - Quick Start Guide

## Installation (1 minute)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up environment
cp .env.example .env

# 3. Edit .env and add your OpenAI API key
# OPENAI_API_KEY=sk-your-api-key-here

# 4. Run the application
streamlit run app.py
```

## First Use (2 minutes)

1. **Open Browser**: Navigate to `http://localhost:8501`

2. **Upload Document**:
   - Go to "Upload & Chat" tab
   - Drag PDF/DOCX/TXT/MD file into upload area
   - Wait for processing (10-30 seconds)

3. **Ask Questions**:
   - Type question in chat input: "What is this document about?"
   - Press Enter
   - View streaming response

4. **Check Sources**:
   - Click "Sources ▼" below response
   - See relevant document chunks

5. **View Metrics**:
   - Click "Query Metrics ▼"
   - See tokens, cost, latency

## Configuration (Optional)

### Change Model (Sidebar)
```
LLM Configuration
├─ Provider: OpenAI ▼
└─ Model: gpt-3.5-turbo ▼  (cheaper)
          gpt-4 ▼           (better quality)
```

### Adjust Parameters (Sidebar)
```
Temperature: 0.7  (creativity)
Top K: 5          (context chunks)
Max Tokens: 500   (response length)
```

### Tune Chunking (Sidebar)
```
Chunk Size: 1000     (segment size)
Chunk Overlap: 200   (overlap for context)
```

## Common Tasks

### Upload Multiple Documents
```
1. Drag multiple files into upload area
2. Each processed separately
3. Switch between docs in sidebar "Documents" section
```

### View Chat History
```
1. Go to "Advanced Features" tab
2. Select "Chat History Viewer"
3. Search or browse past conversations
```

### Track Costs
```
1. Check sidebar "Usage Analytics"
   - Total Cost
   - Total Tokens
   - Query Count

2. OR go to "Advanced Features" → "Cost Analytics"
   - Detailed breakdown per query
```

### Compare Models
```
1. Go to "Advanced Features" tab
2. Select "Model Comparison"
3. Choose two models
4. Enter question
5. Click "Compare Models"
```

## Keyboard Shortcuts

- **Enter**: Send chat message
- **Ctrl+K**: Clear Streamlit cache
- **R**: Rerun app

## Cost Optimization Tips

1. **Use GPT-3.5-Turbo**: 10x cheaper than GPT-4
2. **Reduce Top K**: Use 3-5 chunks instead of 10
3. **Lower Max Tokens**: Set to 300-500 for Q&A
4. **Clear Chat History**: Long context = higher cost
5. **Monitor Analytics**: Check sidebar regularly

## Troubleshooting

### Error: "OPENAI_API_KEY not found"
**Fix**: Add API key to `.env` file
```bash
OPENAI_API_KEY=sk-your-actual-key-here
```

### Error: "python-docx not installed"
**Fix**: Install the package
```bash
pip install python-docx
```

### Document Upload Fails
**Check**:
- File format supported? (PDF, DOCX, TXT, MD)
- File not corrupted?
- File size reasonable? (<50MB)

### High Costs
**Solutions**:
- Switch to `gpt-3.5-turbo`
- Reduce `max_tokens` to 300
- Reduce `top_k` to 3
- Clear chat history

### Slow Responses
**Causes**:
- Large documents (many chunks to search)
- High top_k (more chunks to retrieve)
- GPT-4 (slower than GPT-3.5)

**Solutions**:
- Use smaller chunk size (500-800)
- Reduce top_k to 3-5
- Switch to gpt-3.5-turbo

## Feature Overview

### Implemented ✅
- Document upload (PDF, DOCX, TXT, MD)
- Chat interface with streaming
- Source citations
- Cost tracking
- Model selection (OpenAI)
- Parameter tuning
- Chat history
- Analytics dashboard
- Document management

### Coming Soon 🔜
- Ollama integration (local LLMs)
- HuggingFace integration
- Hybrid search (BM25 + semantic)
- Re-ranking
- Contextual compression
- Multi-document querying

## File Structure

```
chatPDF/
├── app.py                    # Main Streamlit app (985 lines)
├── requirements.txt          # Dependencies
├── .env                      # Your config (create from .env.example)
├── data/                     # Created automatically
│   ├── uploads/              # Uploaded documents
│   └── vector_stores/        # FAISS indices
└── Documentation
    ├── APP_README.md         # Detailed docs
    ├── UI_FEATURES_SUMMARY.md # Feature list
    ├── UI_LAYOUT.md          # UI diagrams
    └── QUICKSTART.md         # This file
```

## Example Session

```
1. Start app:
   $ streamlit run app.py

2. Upload: research_paper.pdf
   ✅ Processed: 15 pages, 150 chunks

3. Ask: "What is the main hypothesis?"
   🤖 Response: "The main hypothesis is..."
   📚 Sources: 3 relevant chunks
   📊 Cost: $0.002 | Tokens: 1,234

4. Ask: "What were the results?"
   🤖 Response: "The results showed..."
   📊 Cost: $0.003 | Tokens: 1,456

5. Check Analytics:
   - Total Queries: 2
   - Total Cost: $0.005
   - Total Tokens: 2,690
```

## Next Steps

1. **Explore Settings**: Try different models and parameters
2. **Upload More Docs**: Test with different file types
3. **Review Analytics**: Understand your usage patterns
4. **Read HLD/LLD**: Learn about RAG architecture
5. **Customize**: Modify app.py for your needs

## Support

- **Documentation**: See APP_README.md
- **Architecture**: See HLD.md and LLD.md
- **UI Details**: See UI_FEATURES_SUMMARY.md
- **Layout**: See UI_LAYOUT.md

---

**Ready to chat with your documents!**

Start with: `streamlit run app.py`
