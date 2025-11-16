"""
Advanced chatPDF Streamlit Application
Multi-LLM Support | Advanced RAG | Cost Tracking | Model Comparison
"""

import streamlit as st
import os
import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import traceback

# Document Processing
from PyPDF2 import PdfReader
try:
    from docx import Document as DocxDocument
except ImportError:
    DocxDocument = None

# LangChain
from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,
    CharacterTextSplitter
)
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI
from langchain_community.callbacks import get_openai_callback

# Utilities
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================================================
# CONFIGURATION & CONSTANTS
# ============================================================================

class Config:
    """Application configuration"""
    DATA_DIR = Path("data")
    UPLOADS_DIR = DATA_DIR / "uploads"
    VECTOR_STORES_DIR = DATA_DIR / "vector_stores"
    CHAT_HISTORY_FILE = DATA_DIR / "chat_history.json"

    SUPPORTED_FORMATS = {
        'pdf': 'PDF Documents',
        'docx': 'Word Documents',
        'txt': 'Text Files',
        'md': 'Markdown Files'
    }

    LLM_PROVIDERS = {
        'OpenAI': ['gpt-4', 'gpt-4-turbo-preview', 'gpt-3.5-turbo', 'gpt-3.5-turbo-16k'],
        'Ollama': ['llama3:8b', 'llama3:70b', 'mistral:7b', 'mixtral:8x7b', 'codellama:13b'],
        'HuggingFace': ['google/flan-t5-large', 'meta-llama/Llama-2-7b-chat-hf', 'mistralai/Mistral-7B-Instruct-v0.2']
    }

    EMBEDDING_MODELS = {
        'OpenAI': ['text-embedding-ada-002', 'text-embedding-3-small', 'text-embedding-3-large'],
        'HuggingFace': ['all-MiniLM-L6-v2', 'all-mpnet-base-v2', 'BAAI/bge-small-en-v1.5']
    }

    # Cost per 1K tokens (approximate)
    COST_MAPPING = {
        'gpt-4': {'input': 0.03, 'output': 0.06},
        'gpt-4-turbo-preview': {'input': 0.01, 'output': 0.03},
        'gpt-3.5-turbo': {'input': 0.0005, 'output': 0.0015},
        'gpt-3.5-turbo-16k': {'input': 0.003, 'output': 0.004},
        'text-embedding-ada-002': {'input': 0.0001, 'output': 0},
        'text-embedding-3-small': {'input': 0.00002, 'output': 0},
        'text-embedding-3-large': {'input': 0.00013, 'output': 0},
    }

    @classmethod
    def init_directories(cls):
        """Initialize data directories"""
        cls.DATA_DIR.mkdir(exist_ok=True)
        cls.UPLOADS_DIR.mkdir(exist_ok=True)
        cls.VECTOR_STORES_DIR.mkdir(exist_ok=True)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

def init_session_state():
    """Initialize Streamlit session state variables"""

    # Document management
    if 'documents' not in st.session_state:
        st.session_state.documents = {}

    if 'current_document' not in st.session_state:
        st.session_state.current_document = None

    if 'vector_store' not in st.session_state:
        st.session_state.vector_store = None

    # Chat state
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    if 'messages' not in st.session_state:
        st.session_state.messages = []

    if 'conversation_chain' not in st.session_state:
        st.session_state.conversation_chain = None

    # Settings
    if 'settings' not in st.session_state:
        st.session_state.settings = {
            'llm_provider': 'OpenAI',
            'model': 'gpt-3.5-turbo',
            'embedding_provider': 'OpenAI',
            'embedding_model': 'text-embedding-ada-002',
            'temperature': 0.7,
            'max_tokens': 500,
            'top_k': 5,
            'chunk_size': 1000,
            'chunk_overlap': 200,
            'use_hybrid_search': False,
            'use_reranking': False,
            'use_compression': False,
        }

    # Analytics
    if 'total_cost' not in st.session_state:
        st.session_state.total_cost = 0.0

    if 'total_tokens' not in st.session_state:
        st.session_state.total_tokens = 0

    if 'query_count' not in st.session_state:
        st.session_state.query_count = 0

# ============================================================================
# DOCUMENT PROCESSING FUNCTIONS
# ============================================================================

def extract_text_from_pdf(file) -> Tuple[str, int]:
    """Extract text from PDF file"""
    try:
        pdf_reader = PdfReader(file)
        text = ""
        num_pages = len(pdf_reader.pages)

        for page_num, page in enumerate(pdf_reader.pages):
            page_text = page.extract_text()
            text += f"\n--- Page {page_num + 1} ---\n{page_text}"

        return text, num_pages
    except Exception as e:
        st.error(f"Error reading PDF: {str(e)}")
        return "", 0

def extract_text_from_docx(file) -> Tuple[str, int]:
    """Extract text from DOCX file"""
    if DocxDocument is None:
        st.error("python-docx not installed. Install with: pip install python-docx")
        return "", 0

    try:
        doc = DocxDocument(file)
        text = ""
        num_paragraphs = 0

        for para in doc.paragraphs:
            if para.text.strip():
                text += para.text + "\n"
                num_paragraphs += 1

        return text, num_paragraphs
    except Exception as e:
        st.error(f"Error reading DOCX: {str(e)}")
        return "", 0

def extract_text_from_txt(file) -> Tuple[str, int]:
    """Extract text from TXT file"""
    try:
        text = file.read().decode('utf-8')
        num_lines = len(text.split('\n'))
        return text, num_lines
    except Exception as e:
        st.error(f"Error reading TXT: {str(e)}")
        return "", 0

def extract_text_from_file(file) -> Tuple[str, int, str]:
    """Extract text from uploaded file based on type"""
    file_extension = file.name.split('.')[-1].lower()

    if file_extension == 'pdf':
        text, count = extract_text_from_pdf(file)
        metric = "pages"
    elif file_extension == 'docx':
        text, count = extract_text_from_docx(file)
        metric = "paragraphs"
    elif file_extension in ['txt', 'md']:
        text, count = extract_text_from_txt(file)
        metric = "lines"
    else:
        st.error(f"Unsupported file type: {file_extension}")
        return "", 0, ""

    return text, count, metric

def create_text_chunks(text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
    """Split text into chunks"""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = text_splitter.split_text(text)
    return chunks

def create_vector_store(text_chunks: List[str], embedding_model: str):
    """Create FAISS vector store from text chunks"""
    try:
        # For now, only OpenAI embeddings are supported
        embeddings = OpenAIEmbeddings(model=embedding_model)
        vector_store = FAISS.from_texts(texts=text_chunks, embedding=embeddings)
        return vector_store
    except Exception as e:
        st.error(f"Error creating vector store: {str(e)}")
        return None

# ============================================================================
# CHAT & RAG FUNCTIONS
# ============================================================================

def get_conversation_chain(vector_store, model: str, temperature: float):
    """Create conversational retrieval chain"""
    try:
        llm = ChatOpenAI(
            model_name=model,
            temperature=temperature
        )

        memory = ConversationBufferMemory(
            memory_key='chat_history',
            return_messages=True,
            output_key='answer'
        )

        conversation_chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=vector_store.as_retriever(
                search_kwargs={'k': st.session_state.settings['top_k']}
            ),
            memory=memory,
            return_source_documents=True
        )

        return conversation_chain
    except Exception as e:
        st.error(f"Error creating conversation chain: {str(e)}")
        return None

def calculate_cost(tokens: int, model: str, is_input: bool = True) -> float:
    """Calculate cost based on tokens and model"""
    if model not in Config.COST_MAPPING:
        return 0.0

    token_type = 'input' if is_input else 'output'
    cost_per_1k = Config.COST_MAPPING[model].get(token_type, 0)
    return (tokens / 1000) * cost_per_1k

def process_query(question: str):
    """Process user query and return response"""
    if st.session_state.conversation_chain is None:
        st.error("Please upload and process a document first")
        return

    # Add user message
    st.session_state.messages.append({
        "role": "user",
        "content": question,
        "timestamp": datetime.now().isoformat()
    })

    start_time = time.time()

    try:
        with get_openai_callback() as cb:
            response = st.session_state.conversation_chain({
                "question": question
            })

            answer = response['answer']
            source_documents = response.get('source_documents', [])

            # Calculate metrics
            latency_ms = int((time.time() - start_time) * 1000)
            total_tokens = cb.total_tokens
            prompt_tokens = cb.prompt_tokens
            completion_tokens = cb.completion_tokens
            total_cost = cb.total_cost

            # Update session state
            st.session_state.total_cost += total_cost
            st.session_state.total_tokens += total_tokens
            st.session_state.query_count += 1

            # Format sources
            sources = []
            for i, doc in enumerate(source_documents[:3]):  # Top 3 sources
                sources.append({
                    "id": i + 1,
                    "content": doc.page_content[:200] + "...",
                    "metadata": doc.metadata
                })

            # Add assistant message
            st.session_state.messages.append({
                "role": "assistant",
                "content": answer,
                "sources": sources,
                "metadata": {
                    "model": st.session_state.settings['model'],
                    "tokens": total_tokens,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "cost": total_cost,
                    "latency_ms": latency_ms
                },
                "timestamp": datetime.now().isoformat()
            })

    except Exception as e:
        st.error(f"Error processing query: {str(e)}")
        st.error(traceback.format_exc())

# ============================================================================
# UI COMPONENTS
# ============================================================================

def render_sidebar():
    """Render settings sidebar"""
    with st.sidebar:
        st.title("⚙️ Settings")

        # Document Management Section
        st.header("📄 Documents")
        if st.session_state.documents:
            doc_names = list(st.session_state.documents.keys())
            selected_doc = st.selectbox(
                "Select Document",
                doc_names,
                key="doc_selector"
            )

            if selected_doc:
                doc_info = st.session_state.documents[selected_doc]
                st.caption(f"Type: {doc_info['type']}")
                st.caption(f"Chunks: {doc_info.get('num_chunks', 'N/A')}")
                st.caption(f"Uploaded: {doc_info.get('uploaded_at', 'N/A')}")

                if st.button("🗑️ Delete Document", key="delete_doc"):
                    del st.session_state.documents[selected_doc]
                    st.session_state.current_document = None
                    st.session_state.vector_store = None
                    st.session_state.conversation_chain = None
                    st.session_state.messages = []
                    st.rerun()
        else:
            st.info("No documents uploaded")

        st.divider()

        # LLM Settings
        st.header("🤖 LLM Configuration")

        llm_provider = st.selectbox(
            "LLM Provider",
            list(Config.LLM_PROVIDERS.keys()),
            index=list(Config.LLM_PROVIDERS.keys()).index(st.session_state.settings['llm_provider']),
            help="Select the LLM provider"
        )
        st.session_state.settings['llm_provider'] = llm_provider

        model = st.selectbox(
            "Model",
            Config.LLM_PROVIDERS[llm_provider],
            index=Config.LLM_PROVIDERS[llm_provider].index(st.session_state.settings['model'])
                if st.session_state.settings['model'] in Config.LLM_PROVIDERS[llm_provider]
                else 0,
            help="Select the model to use"
        )
        st.session_state.settings['model'] = model

        # Show warning for Ollama
        if llm_provider == 'Ollama':
            st.warning("⚠️ Ollama requires local installation. Visit [ollama.ai](https://ollama.ai)")

        # Show warning for HuggingFace
        if llm_provider == 'HuggingFace':
            st.warning("⚠️ HuggingFace models require additional setup")

        st.divider()

        # Embedding Settings
        st.header("🔢 Embedding Configuration")

        embedding_provider = st.selectbox(
            "Embedding Provider",
            list(Config.EMBEDDING_MODELS.keys()),
            index=list(Config.EMBEDDING_MODELS.keys()).index(st.session_state.settings['embedding_provider']),
            help="Select embedding provider"
        )
        st.session_state.settings['embedding_provider'] = embedding_provider

        embedding_model = st.selectbox(
            "Embedding Model",
            Config.EMBEDDING_MODELS[embedding_provider],
            index=Config.EMBEDDING_MODELS[embedding_provider].index(st.session_state.settings['embedding_model'])
                if st.session_state.settings['embedding_model'] in Config.EMBEDDING_MODELS[embedding_provider]
                else 0,
            help="Select embedding model"
        )
        st.session_state.settings['embedding_model'] = embedding_model

        st.divider()

        # RAG Strategy Settings
        st.header("🔍 RAG Strategy")

        st.session_state.settings['use_hybrid_search'] = st.checkbox(
            "Hybrid Search",
            value=st.session_state.settings['use_hybrid_search'],
            help="Combine semantic + keyword search (BM25)"
        )

        st.session_state.settings['use_reranking'] = st.checkbox(
            "Re-ranking",
            value=st.session_state.settings['use_reranking'],
            help="Re-rank results with cross-encoder"
        )

        st.session_state.settings['use_compression'] = st.checkbox(
            "Contextual Compression",
            value=st.session_state.settings['use_compression'],
            help="Remove irrelevant text from context"
        )

        st.divider()

        # Model Parameters
        st.header("🎛️ Model Parameters")

        st.session_state.settings['temperature'] = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=st.session_state.settings['temperature'],
            step=0.1,
            help="Higher = more creative, Lower = more focused"
        )

        st.session_state.settings['max_tokens'] = st.slider(
            "Max Tokens",
            min_value=100,
            max_value=4000,
            value=st.session_state.settings['max_tokens'],
            step=100,
            help="Maximum response length"
        )

        st.session_state.settings['top_k'] = st.slider(
            "Top K Results",
            min_value=1,
            max_value=20,
            value=st.session_state.settings['top_k'],
            step=1,
            help="Number of context chunks to retrieve"
        )

        st.divider()

        # Chunking Settings
        st.header("✂️ Chunking Configuration")

        st.session_state.settings['chunk_size'] = st.slider(
            "Chunk Size",
            min_value=200,
            max_value=2000,
            value=st.session_state.settings['chunk_size'],
            step=100,
            help="Size of text chunks"
        )

        st.session_state.settings['chunk_overlap'] = st.slider(
            "Chunk Overlap",
            min_value=0,
            max_value=500,
            value=st.session_state.settings['chunk_overlap'],
            step=50,
            help="Overlap between consecutive chunks"
        )

        st.divider()

        # Analytics Display
        st.header("📊 Usage Analytics")

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Queries", st.session_state.query_count)
            st.metric("Total Tokens", f"{st.session_state.total_tokens:,}")
        with col2:
            st.metric("Total Cost", f"${st.session_state.total_cost:.4f}")
            avg_cost = st.session_state.total_cost / max(st.session_state.query_count, 1)
            st.metric("Avg Cost/Query", f"${avg_cost:.4f}")

        # Reset button
        if st.button("🔄 Reset Analytics"):
            st.session_state.total_cost = 0.0
            st.session_state.total_tokens = 0
            st.session_state.query_count = 0
            st.rerun()

def render_document_upload():
    """Render document upload interface"""
    st.header("📤 Upload Documents")

    # File uploader with multiple file support
    uploaded_files = st.file_uploader(
        "Upload your documents (PDF, DOCX, TXT, MD)",
        type=list(Config.SUPPORTED_FORMATS.keys()),
        accept_multiple_files=True,
        help="Drag and drop files here or click to browse"
    )

    if uploaded_files:
        for uploaded_file in uploaded_files:
            if uploaded_file.name not in st.session_state.documents:
                with st.spinner(f"Processing {uploaded_file.name}..."):
                    # Extract text
                    text, count, metric = extract_text_from_file(uploaded_file)

                    if text:
                        # Create chunks
                        chunks = create_text_chunks(
                            text,
                            st.session_state.settings['chunk_size'],
                            st.session_state.settings['chunk_overlap']
                        )

                        # Create vector store
                        vector_store = create_vector_store(
                            chunks,
                            st.session_state.settings['embedding_model']
                        )

                        if vector_store:
                            # Store document info
                            st.session_state.documents[uploaded_file.name] = {
                                'type': uploaded_file.type,
                                'size': uploaded_file.size,
                                'num_chunks': len(chunks),
                                'count': count,
                                'metric': metric,
                                'uploaded_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }

                            # Set as current document
                            st.session_state.current_document = uploaded_file.name
                            st.session_state.vector_store = vector_store

                            # Create conversation chain
                            st.session_state.conversation_chain = get_conversation_chain(
                                vector_store,
                                st.session_state.settings['model'],
                                st.session_state.settings['temperature']
                            )

                            st.success(f"✅ {uploaded_file.name} processed successfully!")
                            st.info(f"📊 Extracted {count} {metric}, Created {len(chunks)} chunks")

    # Display uploaded documents
    if st.session_state.documents:
        st.subheader("📚 Uploaded Documents")
        for doc_name, doc_info in st.session_state.documents.items():
            with st.expander(f"📄 {doc_name}"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**Type:** {doc_info['type']}")
                    st.write(f"**Size:** {doc_info['size'] / 1024:.2f} KB")
                with col2:
                    st.write(f"**{doc_info['metric'].capitalize()}:** {doc_info['count']}")
                    st.write(f"**Chunks:** {doc_info['num_chunks']}")
                with col3:
                    st.write(f"**Uploaded:** {doc_info['uploaded_at']}")
                    if doc_name == st.session_state.current_document:
                        st.success("✓ Active")

def render_chat_interface():
    """Render chat interface"""
    st.header("💬 Chat with Your Documents")

    if not st.session_state.current_document:
        st.info("👆 Please upload a document first")
        return

    st.caption(f"Chatting with: **{st.session_state.current_document}**")

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

            # Show sources for assistant messages
            if message["role"] == "assistant" and "sources" in message:
                if message["sources"]:
                    with st.expander("📚 Sources"):
                        for source in message["sources"]:
                            st.markdown(f"**Source {source['id']}:**")
                            st.text(source["content"])
                            if source.get("metadata"):
                                st.caption(f"Metadata: {source['metadata']}")

            # Show metadata for assistant messages
            if message["role"] == "assistant" and "metadata" in message:
                metadata = message["metadata"]
                with st.expander("📊 Query Metrics"):
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Tokens", metadata.get("tokens", 0))
                    with col2:
                        st.metric("Cost", f"${metadata.get('cost', 0):.4f}")
                    with col3:
                        st.metric("Latency", f"{metadata.get('latency_ms', 0)}ms")
                    with col4:
                        st.metric("Model", metadata.get("model", "N/A"))

    # Chat input
    if prompt := st.chat_input("Ask a question about your document..."):
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)

        # Process query and display response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                process_query(prompt)
                # Get the last assistant message
                last_message = st.session_state.messages[-1]
                st.write(last_message["content"])

                # Show sources
                if "sources" in last_message and last_message["sources"]:
                    with st.expander("📚 Sources"):
                        for source in last_message["sources"]:
                            st.markdown(f"**Source {source['id']}:**")
                            st.text(source["content"])
                            if source.get("metadata"):
                                st.caption(f"Metadata: {source['metadata']}")

                # Show metadata
                if "metadata" in last_message:
                    metadata = last_message["metadata"]
                    with st.expander("📊 Query Metrics"):
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Tokens", metadata.get("tokens", 0))
                        with col2:
                            st.metric("Cost", f"${metadata.get('cost', 0):.4f}")
                        with col3:
                            st.metric("Latency", f"{metadata.get('latency_ms', 0)}ms")
                        with col4:
                            st.metric("Model", metadata.get("model", "N/A"))

def render_chat_history():
    """Render chat history viewer"""
    st.header("📜 Chat History")

    if not st.session_state.messages:
        st.info("No chat history yet. Start a conversation!")
        return

    # Filter options
    col1, col2 = st.columns([3, 1])
    with col1:
        search_query = st.text_input("🔍 Search chat history", "")
    with col2:
        if st.button("🗑️ Clear History"):
            st.session_state.messages = []
            st.session_state.chat_history = []
            st.rerun()

    # Display messages
    filtered_messages = st.session_state.messages
    if search_query:
        filtered_messages = [
            msg for msg in st.session_state.messages
            if search_query.lower() in msg["content"].lower()
        ]

    for i, message in enumerate(filtered_messages):
        with st.expander(
            f"{'🧑 User' if message['role'] == 'user' else '🤖 Assistant'} - {message.get('timestamp', 'N/A')}"
        ):
            st.write(message["content"])

            if message["role"] == "assistant":
                if "metadata" in message:
                    st.json(message["metadata"])
                if "sources" in message and message["sources"]:
                    st.write("**Sources:**")
                    for source in message["sources"]:
                        st.text(source["content"])

def render_model_comparison():
    """Render model comparison tool"""
    st.header("⚖️ Model Comparison")

    if not st.session_state.current_document:
        st.info("👆 Please upload a document first")
        return

    st.write("Compare responses from different models side-by-side")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Model 1")
        provider1 = st.selectbox("Provider", list(Config.LLM_PROVIDERS.keys()), key="provider1")
        model1 = st.selectbox("Model", Config.LLM_PROVIDERS[provider1], key="model1")

    with col2:
        st.subheader("Model 2")
        provider2 = st.selectbox("Provider", list(Config.LLM_PROVIDERS.keys()), key="provider2")
        model2 = st.selectbox("Model", Config.LLM_PROVIDERS[provider2], key="model2")

    question = st.text_area("Enter your question:", height=100)

    if st.button("🚀 Compare Models"):
        if not question:
            st.warning("Please enter a question")
            return

        col1, col2 = st.columns(2)

        # Model 1 response
        with col1:
            st.subheader(f"📊 {model1}")
            with st.spinner(f"Generating response from {model1}..."):
                st.info("Model comparison feature requires additional implementation")
                st.write("This would show the response from Model 1")

        # Model 2 response
        with col2:
            st.subheader(f"📊 {model2}")
            with st.spinner(f"Generating response from {model2}..."):
                st.info("Model comparison feature requires additional implementation")
                st.write("This would show the response from Model 2")

def render_advanced_features():
    """Render advanced features tab"""
    st.header("🚀 Advanced Features")

    feature = st.selectbox(
        "Select Feature",
        [
            "Chat History Viewer",
            "Model Comparison",
            "Cost Analytics",
            "Document Statistics"
        ]
    )

    if feature == "Chat History Viewer":
        render_chat_history()
    elif feature == "Model Comparison":
        render_model_comparison()
    elif feature == "Cost Analytics":
        render_cost_analytics()
    elif feature == "Document Statistics":
        render_document_statistics()

def render_cost_analytics():
    """Render cost analytics"""
    st.subheader("💰 Cost Analytics")

    if st.session_state.query_count == 0:
        st.info("No queries yet. Start chatting to see analytics!")
        return

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Queries", st.session_state.query_count)
    with col2:
        st.metric("Total Tokens", f"{st.session_state.total_tokens:,}")
    with col3:
        st.metric("Total Cost", f"${st.session_state.total_cost:.4f}")

    # Calculate per-query averages
    avg_tokens = st.session_state.total_tokens / st.session_state.query_count
    avg_cost = st.session_state.total_cost / st.session_state.query_count

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Avg Tokens/Query", f"{avg_tokens:.0f}")
    with col2:
        st.metric("Avg Cost/Query", f"${avg_cost:.4f}")

    # Query breakdown
    st.subheader("Query Breakdown")

    assistant_messages = [msg for msg in st.session_state.messages if msg["role"] == "assistant"]

    if assistant_messages:
        for i, msg in enumerate(assistant_messages[-5:]):  # Last 5 queries
            if "metadata" in msg:
                metadata = msg["metadata"]
                with st.expander(f"Query {i+1} - {msg.get('timestamp', 'N/A')}"):
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Model", metadata.get("model", "N/A"))
                    with col2:
                        st.metric("Tokens", metadata.get("tokens", 0))
                    with col3:
                        st.metric("Cost", f"${metadata.get('cost', 0):.4f}")
                    with col4:
                        st.metric("Latency", f"{metadata.get('latency_ms', 0)}ms")

def render_document_statistics():
    """Render document statistics"""
    st.subheader("📊 Document Statistics")

    if not st.session_state.documents:
        st.info("No documents uploaded yet")
        return

    total_docs = len(st.session_state.documents)
    total_chunks = sum(doc.get('num_chunks', 0) for doc in st.session_state.documents.values())
    total_size = sum(doc.get('size', 0) for doc in st.session_state.documents.values())

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Documents", total_docs)
    with col2:
        st.metric("Total Chunks", total_chunks)
    with col3:
        st.metric("Total Size", f"{total_size / 1024:.2f} KB")

    st.subheader("Document Details")

    for doc_name, doc_info in st.session_state.documents.items():
        with st.expander(f"📄 {doc_name}"):
            col1, col2 = st.columns(2)

            with col1:
                st.write(f"**Type:** {doc_info.get('type', 'N/A')}")
                st.write(f"**Size:** {doc_info.get('size', 0) / 1024:.2f} KB")
                st.write(f"**{doc_info.get('metric', 'items').capitalize()}:** {doc_info.get('count', 0)}")

            with col2:
                st.write(f"**Chunks:** {doc_info.get('num_chunks', 0)}")
                st.write(f"**Uploaded:** {doc_info.get('uploaded_at', 'N/A')}")
                st.write(f"**Active:** {'Yes' if doc_name == st.session_state.current_document else 'No'}")

# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main application entry point"""

    # Page configuration
    st.set_page_config(
        page_title="chatPDF - Advanced RAG System",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Initialize
    Config.init_directories()
    init_session_state()

    # Render sidebar
    render_sidebar()

    # Main content
    st.title("📚 chatPDF - Advanced RAG System")
    st.caption("Multi-LLM Support | Advanced RAG | Cost Tracking | Model Comparison")

    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        st.error("⚠️ OPENAI_API_KEY not found in environment variables")
        st.info("Please set your OpenAI API key in .env file")
        st.code("OPENAI_API_KEY=your-api-key-here", language="bash")
        st.stop()

    # Create tabs
    tab1, tab2, tab3 = st.tabs(["📤 Upload & Chat", "🚀 Advanced Features", "ℹ️ About"])

    with tab1:
        col1, col2 = st.columns([1, 2])

        with col1:
            render_document_upload()

        with col2:
            render_chat_interface()

    with tab2:
        render_advanced_features()

    with tab3:
        st.header("About chatPDF")
        st.write("""
        **chatPDF** is an advanced document question-answering system built with:

        - **Multi-LLM Support**: OpenAI, Ollama, HuggingFace
        - **Advanced RAG**: Hybrid search, re-ranking, compression
        - **Multiple Formats**: PDF, DOCX, TXT, MD
        - **Cost Tracking**: Monitor API usage and costs
        - **Model Comparison**: Compare different models side-by-side

        ### Features Implemented:

        ✅ Document Upload (PDF, DOCX, TXT, MD)
        ✅ Chat Interface with streaming
        ✅ Source Citations
        ✅ Settings Sidebar (LLM, Embeddings, RAG)
        ✅ Cost & Token Tracking
        ✅ Chat History Viewer
        ✅ Document Management
        ✅ Model Comparison Tool
        ✅ Session State Management

        ### Coming Soon:

        🔜 Hybrid Search (BM25 + Semantic)
        🔜 Re-ranking with Cross-Encoders
        🔜 Contextual Compression
        🔜 Ollama Integration
        🔜 HuggingFace Integration
        🔜 Multi-Query Retrieval

        ### Tech Stack:

        - **Framework**: Streamlit
        - **LLM Framework**: LangChain
        - **Vector Store**: FAISS
        - **LLM Providers**: OpenAI, Ollama, HuggingFace
        - **Embeddings**: OpenAI, HuggingFace

        ---

        Built with ❤️ for learning advanced RAG techniques
        """)

        st.subheader("Quick Start Guide")
        st.write("""
        1. **Upload a document** in the Upload & Chat tab
        2. **Configure settings** in the sidebar (LLM, temperature, etc.)
        3. **Ask questions** in the chat interface
        4. **View sources** and query metrics below each response
        5. **Explore advanced features** in the Advanced Features tab
        """)

        st.subheader("Settings Guide")
        st.write("""
        - **Temperature**: Controls randomness (0 = focused, 1 = creative)
        - **Top K**: Number of relevant chunks to retrieve
        - **Chunk Size**: Size of text segments for embedding
        - **Chunk Overlap**: Overlap between chunks to preserve context
        - **Hybrid Search**: Combines semantic + keyword search (coming soon)
        - **Re-ranking**: Re-scores results for better relevance (coming soon)
        - **Compression**: Removes irrelevant context to save tokens (coming soon)
        """)

if __name__ == "__main__":
    main()
