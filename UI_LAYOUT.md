# chatPDF Streamlit UI - Layout Guide

## Main Application Layout

```
┌────────────────────────────────────────────────────────────────────────────┐
│                     📚 chatPDF - Advanced RAG System                       │
│            Multi-LLM Support | Advanced RAG | Cost Tracking                │
└────────────────────────────────────────────────────────────────────────────┘

┌──────────────┐  ┌─────────────────────────────────────────────────────────┐
│              │  │                                                           │
│   SIDEBAR    │  │                     MAIN CONTENT AREA                     │
│              │  │                                                           │
│ ⚙️ Settings  │  │  [📤 Upload & Chat] [🚀 Advanced Features] [ℹ️ About]   │
│              │  │                                                           │
│ ┌──────────┐ │  │ ┌─────────────────────────────────────────────────────┐ │
│ │📄 Docs   │ │  │ │                                                     │ │
│ │          │ │  │ │         CONTENT BASED ON SELECTED TAB               │ │
│ │ Select:  │ │  │ │                                                     │ │
│ │  [▼]     │ │  │ │                                                     │ │
│ │          │ │  │ │                                                     │ │
│ │🗑️ Delete │ │  │ │                                                     │ │
│ └──────────┘ │  │ └─────────────────────────────────────────────────────┘ │
│              │  │                                                           │
│ ┌──────────┐ │  │                                                           │
│ │🤖 LLM    │ │  │                                                           │
│ │          │ │  │                                                           │
│ │Provider: │ │  │                                                           │
│ │  [▼]     │ │  │                                                           │
│ │Model:    │ │  │                                                           │
│ │  [▼]     │ │  │                                                           │
│ └──────────┘ │  │                                                           │
│              │  │                                                           │
│ ┌──────────┐ │  │                                                           │
│ │🔢 Embed  │ │  │                                                           │
│ │          │ │  │                                                           │
│ │Provider: │ │  │                                                           │
│ │  [▼]     │ │  │                                                           │
│ │Model:    │ │  │                                                           │
│ │  [▼]     │ │  │                                                           │
│ └──────────┘ │  │                                                           │
│              │  │                                                           │
│ ┌──────────┐ │  │                                                           │
│ │🔍 RAG    │ │  │                                                           │
│ │          │ │  │                                                           │
│ │☐ Hybrid  │ │  │                                                           │
│ │☐ Rerank  │ │  │                                                           │
│ │☐ Compress│ │  │                                                           │
│ └──────────┘ │  │                                                           │
│              │  │                                                           │
│ ┌──────────┐ │  │                                                           │
│ │🎛️ Params │ │  │                                                           │
│ │          │ │  │                                                           │
│ │Temp: ━━○ │ │  │                                                           │
│ │Tokens:━○ │ │  │                                                           │
│ │Top K: ━○ │ │  │                                                           │
│ └──────────┘ │  │                                                           │
│              │  │                                                           │
│ ┌──────────┐ │  │                                                           │
│ │✂️ Chunk  │ │  │                                                           │
│ │          │ │  │                                                           │
│ │Size: ━━○ │ │  │                                                           │
│ │Overlap:━○│ │  │                                                           │
│ └──────────┘ │  │                                                           │
│              │  │                                                           │
│ ┌──────────┐ │  │                                                           │
│ │📊 Stats  │ │  │                                                           │
│ │          │ │  │                                                           │
│ │Queries:  │ │  │                                                           │
│ │  42      │ │  │                                                           │
│ │Tokens:   │ │  │                                                           │
│ │  15,234  │ │  │                                                           │
│ │Cost:     │ │  │                                                           │
│ │  $0.45   │ │  │                                                           │
│ │          │ │  │                                                           │
│ │🔄 Reset  │ │  │                                                           │
│ └──────────┘ │  │                                                           │
│              │  │                                                           │
└──────────────┘  └─────────────────────────────────────────────────────────┘
```

---

## Tab 1: Upload & Chat

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          📤 Upload & Chat Tab                               │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────┬───────────────────────────────────────────────────────┐
│                     │                                                       │
│  UPLOAD SECTION     │              CHAT SECTION                             │
│     (Col 1)         │                (Col 2)                                │
│                     │                                                       │
│ ┌─────────────────┐ │  ┌─────────────────────────────────────────────────┐ │
│ │ 📤 Upload Docs  │ │  │ 💬 Chat with Your Documents                     │ │
│ │                 │ │  │ Chatting with: document.pdf                     │ │
│ │ ┌─────────────┐ │ │  └─────────────────────────────────────────────────┘ │
│ │ │             │ │ │                                                       │
│ │ │   Drag &    │ │ │  ┌───────────────────────────────────────────────┐   │
│ │ │    Drop     │ │ │  │ 🧑 User                                       │   │
│ │ │   or Click  │ │ │  │ What are the main findings?                   │   │
│ │ │             │ │ │  └───────────────────────────────────────────────┘   │
│ │ │   📁 PDF    │ │ │                                                       │
│ │ │   📁 DOCX   │ │ │  ┌───────────────────────────────────────────────┐   │
│ │ │   📁 TXT    │ │ │  │ 🤖 Assistant                                  │   │
│ │ │   📁 MD     │ │ │  │ Based on the document, the main findings...   │   │
│ │ │             │ │ │  │                                               │   │
│ │ └─────────────┘ │ │  │ ┌───────────────────────────────────────────┐ │   │
│ └─────────────────┘ │  │ │ 📚 Sources ▼                              │ │   │
│                     │  │ │ Source 1: [relevant text excerpt...]      │ │   │
│ ┌─────────────────┐ │  │ │ Source 2: [relevant text excerpt...]      │ │   │
│ │ 📚 Uploaded     │ │  │ └───────────────────────────────────────────┘ │   │
│ │    Documents    │ │  │                                               │   │
│ │                 │ │  │ ┌───────────────────────────────────────────┐ │   │
│ │ 📄 doc1.pdf ▼   │ │  │ │ 📊 Query Metrics ▼                        │ │   │
│ │ Type: PDF       │ │  │ │ Tokens: 1,234 | Cost: $0.002             │ │   │
│ │ Size: 1.2 MB    │ │  │ │ Latency: 1,234ms | Model: gpt-3.5-turbo  │ │   │
│ │ Chunks: 150     │ │  │ └───────────────────────────────────────────┘ │   │
│ │ ✓ Active        │ │  │                                               │   │
│ │                 │ │  └───────────────────────────────────────────────┘   │
│ │ 📄 doc2.docx ▼  │ │                                                       │
│ │ Type: DOCX      │ │  ┌───────────────────────────────────────────────┐   │
│ │ Size: 0.8 MB    │ │  │ 🧑 User                                       │   │
│ │ Chunks: 98      │ │  │ Tell me more about...                         │   │
│ └─────────────────┘ │  └───────────────────────────────────────────────┘   │
│                     │                                                       │
│                     │  ┌─────────────────────────────────────────────────┐ │
│                     │  │ Ask a question about your document...           │ │
│                     │  └─────────────────────────────────────────────────┘ │
│                     │                                                       │
└─────────────────────┴───────────────────────────────────────────────────────┘
```

---

## Tab 2: Advanced Features

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       🚀 Advanced Features Tab                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ Select Feature: [Chat History Viewer ▼]                                    │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  FEATURE: CHAT HISTORY VIEWER                                               │
│                                                                             │
│  ┌───────────────────────────────────┬───────────────┐                     │
│  │ 🔍 Search chat history            │ 🗑️ Clear     │                     │
│  └───────────────────────────────────┴───────────────┘                     │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 🧑 User - 2025-11-16 10:30:00 ▼                                     │   │
│  │ What are the main findings?                                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 🤖 Assistant - 2025-11-16 10:30:15 ▼                                │   │
│  │ Based on the document, the main findings are...                      │   │
│  │ Metadata: {"model": "gpt-3.5-turbo", "cost": 0.002}                 │   │
│  │ Sources: [Source 1, Source 2]                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  FEATURE: MODEL COMPARISON                                                  │
│                                                                             │
│  ┌──────────────────────────────┬──────────────────────────────┐           │
│  │ Model 1                      │ Model 2                      │           │
│  │ Provider: [OpenAI ▼]         │ Provider: [OpenAI ▼]         │           │
│  │ Model: [gpt-4 ▼]             │ Model: [gpt-3.5-turbo ▼]     │           │
│  └──────────────────────────────┴──────────────────────────────┘           │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────┐     │
│  │ Enter your question:                                              │     │
│  │ [What are the key insights from this document?            ]      │     │
│  └───────────────────────────────────────────────────────────────────┘     │
│                                                                             │
│  [🚀 Compare Models]                                                        │
│                                                                             │
│  ┌──────────────────────────────┬──────────────────────────────┐           │
│  │ 📊 gpt-4                     │ 📊 gpt-3.5-turbo             │           │
│  │                              │                              │           │
│  │ Response from GPT-4...       │ Response from GPT-3.5...     │           │
│  │                              │                              │           │
│  │ Cost: $0.015                 │ Cost: $0.002                 │           │
│  │ Tokens: 1,500                │ Tokens: 1,200                │           │
│  │ Latency: 2,345ms             │ Latency: 1,234ms             │           │
│  └──────────────────────────────┴──────────────────────────────┘           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  FEATURE: COST ANALYTICS                                                    │
│                                                                             │
│  ┌──────────────┬──────────────┬──────────────┐                            │
│  │ Total Queries│ Total Tokens │ Total Cost   │                            │
│  │     42       │   15,234     │   $0.4523    │                            │
│  └──────────────┴──────────────┴──────────────┘                            │
│                                                                             │
│  ┌──────────────────┬──────────────────┐                                   │
│  │ Avg Tokens/Query │ Avg Cost/Query   │                                   │
│  │      363         │    $0.0108       │                                   │
│  └──────────────────┴──────────────────┘                                   │
│                                                                             │
│  Query Breakdown                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Query 1 - 2025-11-16 10:30:00 ▼                                     │   │
│  │ Model: gpt-3.5-turbo | Tokens: 1,234 | Cost: $0.002 | 1,234ms     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  FEATURE: DOCUMENT STATISTICS                                               │
│                                                                             │
│  ┌──────────────┬──────────────┬──────────────┐                            │
│  │Total Documents│ Total Chunks │  Total Size  │                            │
│  │      3       │     450      │   2.5 MB     │                            │
│  └──────────────┴──────────────┴──────────────┘                            │
│                                                                             │
│  Document Details                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 📄 document1.pdf ▼                                                   │   │
│  │ Type: application/pdf        | Chunks: 150                          │   │
│  │ Size: 1.2 MB                 | Uploaded: 2025-11-16 10:00:00       │   │
│  │ Pages: 15                    | Active: Yes                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Tab 3: About

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              ℹ️ About Tab                                   │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  About chatPDF                                                              │
│                                                                             │
│  chatPDF is an advanced document question-answering system built with:      │
│                                                                             │
│  • Multi-LLM Support: OpenAI, Ollama, HuggingFace                           │
│  • Advanced RAG: Hybrid search, re-ranking, compression                     │
│  • Multiple Formats: PDF, DOCX, TXT, MD                                     │
│  • Cost Tracking: Monitor API usage and costs                               │
│  • Model Comparison: Compare different models side-by-side                  │
│                                                                             │
│  Features Implemented:                                                      │
│  ✅ Document Upload (PDF, DOCX, TXT, MD)                                    │
│  ✅ Chat Interface with streaming                                           │
│  ✅ Source Citations                                                        │
│  ✅ Settings Sidebar (LLM, Embeddings, RAG)                                 │
│  ✅ Cost & Token Tracking                                                   │
│  ✅ Chat History Viewer                                                     │
│  ✅ Document Management                                                     │
│  ✅ Model Comparison Tool                                                   │
│  ✅ Session State Management                                                │
│                                                                             │
│  Quick Start Guide                                                          │
│  1. Upload a document in the Upload & Chat tab                              │
│  2. Configure settings in the sidebar (LLM, temperature, etc.)              │
│  3. Ask questions in the chat interface                                     │
│  4. View sources and query metrics below each response                      │
│  5. Explore advanced features in the Advanced Features tab                  │
│                                                                             │
│  Settings Guide                                                             │
│  • Temperature: Controls randomness (0 = focused, 1 = creative)             │
│  • Top K: Number of relevant chunks to retrieve                             │
│  • Chunk Size: Size of text segments for embedding                          │
│  • Chunk Overlap: Overlap between chunks to preserve context                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Mobile/Responsive Layout

Streamlit automatically handles responsive design. On smaller screens:

```
┌──────────────────────────┐
│ 📚 chatPDF               │
├──────────────────────────┤
│ [☰ Sidebar Toggle]       │
├──────────────────────────┤
│ [Tab 1] [Tab 2] [Tab 3]  │
├──────────────────────────┤
│                          │
│  Content Area            │
│  (full width)            │
│                          │
│  Upload section          │
│  (stacked vertically)    │
│                          │
│  Chat section            │
│  (stacked below)         │
│                          │
└──────────────────────────┘
```

---

## Color Scheme

Streamlit default theme (customizable):
- **Background**: White (#FFFFFF)
- **Primary**: Red (#FF4B4B)
- **Secondary**: Gray (#F0F2F6)
- **Text**: Black (#262730)
- **Success**: Green (#00C851)
- **Warning**: Orange (#FFBB33)
- **Error**: Red (#FF4444)

---

## Interactive Elements

### Buttons
```
┌─────────────┐
│ 🚀 Action   │
└─────────────┘
```

### Sliders
```
Temperature: 0.0 ━━━━━●━━━━ 1.0
             (0.7)
```

### Dropdowns
```
┌─────────────────────┐
│ OpenAI          ▼   │
└─────────────────────┘
```

### Checkboxes
```
☑ Hybrid Search
☐ Re-ranking
☐ Compression
```

### File Upload
```
┌─────────────────────────┐
│                         │
│   Drag and drop files   │
│         or              │
│   Browse Files          │
│                         │
│  Supported: PDF, DOCX,  │
│         TXT, MD         │
└─────────────────────────┘
```

### Chat Input
```
┌───────────────────────────────────────┐
│ Ask a question about your document... │
└───────────────────────────────────────┘
```

---

## Status Indicators

### Processing
```
⏳ Processing document.pdf...
```

### Success
```
✅ document.pdf processed successfully!
📊 Extracted 15 pages, Created 150 chunks
```

### Error
```
❌ Error reading PDF: Invalid file format
```

### Info
```
ℹ️ No documents uploaded yet
```

### Warning
```
⚠️ Ollama requires local installation. Visit ollama.ai
```

---

## Navigation Flow

```
Landing
  │
  ├─→ Upload Document
  │     │
  │     ├─→ Processing
  │     │     │
  │     │     └─→ Success → Chat Interface
  │     │
  │     └─→ Error → Retry
  │
  ├─→ Configure Settings (Sidebar)
  │     │
  │     ├─→ Select LLM
  │     ├─→ Adjust Parameters
  │     └─→ Apply Changes
  │
  ├─→ Chat with Document
  │     │
  │     ├─→ Ask Question
  │     ├─→ View Response
  │     ├─→ View Sources
  │     └─→ View Metrics
  │
  └─→ Advanced Features
        │
        ├─→ Chat History
        ├─→ Model Comparison
        ├─→ Cost Analytics
        └─→ Document Stats
```

---

## Keyboard Shortcuts

Streamlit built-in shortcuts:
- **Enter**: Submit chat message
- **Ctrl+K**: Clear cache
- **R**: Rerun app
- **C**: Clear cache

---

## Best Practices for Users

1. **Start Simple**: Upload one document, use default settings
2. **Experiment**: Try different models and parameters
3. **Monitor Costs**: Check analytics regularly
4. **Optimize**: Adjust chunk size and top-k based on results
5. **Compare**: Use model comparison to find best option
6. **Review**: Check sources to verify accuracy

---

This layout provides a clean, functional interface that makes it easy to:
- Upload and manage documents
- Configure RAG and LLM settings
- Chat with documents
- Track costs and performance
- Compare different approaches
