"""Document processing service for chatPDF system.

This module handles document upload, text extraction, chunking, and metadata management.
Based on HLD Section 2.2.2 and LLD Section 3, Class 4.1.
"""

import os
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime
import asyncio

# Document processing libraries
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    from docx import Document as DocxDocument
except ImportError:
    DocxDocument = None

# LangChain text splitters
from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,
    TokenTextSplitter,
)

try:
    from langchain_experimental.text_splitter import SemanticChunker
except ImportError:
    SemanticChunker = None


@dataclass
class DocumentChunk:
    """Represents a chunk of text from a document."""

    chunk_id: str
    document_id: str
    text: str
    metadata: Dict[str, Any]
    chunk_index: int
    start_char: int
    end_char: int


@dataclass
class Document:
    """Represents a processed document."""

    id: str
    filename: str
    file_path: str
    file_type: str
    file_size: int
    num_chunks: Optional[int] = None
    num_pages: Optional[int] = None
    embedding_model: Optional[str] = None
    index_path: Optional[str] = None
    created_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class DocumentService:
    """Service for document processing and management.

    Responsibilities:
    - Document upload handling
    - Format detection (PDF, DOCX, TXT, MD)
    - Text extraction
    - Multiple chunking strategies
    - Metadata extraction
    - Document deletion
    """

    SUPPORTED_FORMATS = {
        'pdf': 'application/pdf',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'txt': 'text/plain',
        'md': 'text/markdown'
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the DocumentService.

        Args:
            config: Configuration dictionary containing:
                - upload_folder: Directory for uploaded files (default: ./data/uploads)
                - chunk_size: Default chunk size in characters (default: 1000)
                - chunk_overlap: Overlap between chunks (default: 200)
                - max_file_size: Maximum file size in MB (default: 50)
        """
        self.config = config or {}
        self.upload_folder = Path(self.config.get('upload_folder', './data/uploads'))
        self.chunk_size = self.config.get('chunk_size', 1000)
        self.chunk_overlap = self.config.get('chunk_overlap', 200)
        self.max_file_size = self.config.get('max_file_size', 50) * 1024 * 1024  # Convert to bytes

        # Ensure upload directory exists
        self.upload_folder.mkdir(parents=True, exist_ok=True)

        # Initialize extractors
        self._init_extractors()

    def _init_extractors(self) -> None:
        """Initialize document extractors for different file types."""
        self.extractors = {
            'pdf': self._extract_pdf,
            'docx': self._extract_docx,
            'txt': self._extract_txt,
            'md': self._extract_markdown
        }

    async def upload_document(
        self,
        file_data: bytes,
        filename: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Document:
        """Upload and process a document.

        Args:
            file_data: Binary file data
            filename: Original filename
            metadata: Optional metadata dictionary

        Returns:
            Document object with processing results

        Raises:
            ValueError: If file type not supported or file too large
            IOError: If file operations fail
        """
        # Validate file
        file_type = self._detect_file_type(filename)
        file_size = len(file_data)

        if file_size > self.max_file_size:
            raise ValueError(
                f"File size ({file_size / 1024 / 1024:.2f} MB) exceeds "
                f"maximum allowed size ({self.max_file_size / 1024 / 1024:.2f} MB)"
            )

        # Generate document ID
        doc_id = self._generate_document_id(filename, file_data)

        # Save file
        file_path = self.upload_folder / f"{doc_id}_{filename}"

        try:
            with open(file_path, 'wb') as f:
                f.write(file_data)
        except Exception as e:
            raise IOError(f"Failed to save file: {str(e)}")

        # Create document object
        document = Document(
            id=doc_id,
            filename=filename,
            file_path=str(file_path),
            file_type=file_type,
            file_size=file_size,
            created_at=datetime.now(),
            metadata=metadata or {}
        )

        return document

    async def extract_text(
        self,
        file_path: str,
        file_type: str
    ) -> str:
        """Extract text from a document.

        Args:
            file_path: Path to the document file
            file_type: Type of document (pdf, docx, txt, md)

        Returns:
            Extracted text as string

        Raises:
            ValueError: If file type not supported
            IOError: If extraction fails
        """
        if file_type not in self.extractors:
            raise ValueError(f"Unsupported file type: {file_type}")

        extractor = self.extractors[file_type]

        try:
            # Run extraction in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            text = await loop.run_in_executor(None, extractor, file_path)
            return text
        except Exception as e:
            raise IOError(f"Failed to extract text from {file_type}: {str(e)}")

    def _extract_pdf(self, file_path: str) -> str:
        """Extract text from PDF file.

        Args:
            file_path: Path to PDF file

        Returns:
            Extracted text
        """
        if PyPDF2 is None:
            raise ImportError("PyPDF2 is required for PDF extraction. Install with: pip install PyPDF2")

        text_parts = []

        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)

            for page_num, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

        return "\n\n".join(text_parts)

    def _extract_docx(self, file_path: str) -> str:
        """Extract text from DOCX file.

        Args:
            file_path: Path to DOCX file

        Returns:
            Extracted text
        """
        if DocxDocument is None:
            raise ImportError("python-docx is required for DOCX extraction. Install with: pip install python-docx")

        doc = DocxDocument(file_path)
        text_parts = []

        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_parts.append(paragraph.text)

        return "\n\n".join(text_parts)

    def _extract_txt(self, file_path: str) -> str:
        """Extract text from TXT file.

        Args:
            file_path: Path to TXT file

        Returns:
            File contents
        """
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            return file.read()

    def _extract_markdown(self, file_path: str) -> str:
        """Extract text from Markdown file.

        Args:
            file_path: Path to Markdown file

        Returns:
            File contents
        """
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            return file.read()

    def chunk_text(
        self,
        text: str,
        document_id: str,
        strategy: str = "recursive",
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        embedding_model: Optional[Any] = None
    ) -> List[DocumentChunk]:
        """Split text into chunks using specified strategy.

        Args:
            text: Text to chunk
            document_id: ID of the source document
            strategy: Chunking strategy ("recursive", "semantic", "token")
            chunk_size: Size of chunks (uses default if None)
            chunk_overlap: Overlap between chunks (uses default if None)
            embedding_model: Required for semantic chunking

        Returns:
            List of DocumentChunk objects

        Raises:
            ValueError: If strategy is invalid or required parameters missing
        """
        chunk_size = chunk_size or self.chunk_size
        chunk_overlap = chunk_overlap or self.chunk_overlap

        if strategy == "recursive":
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                length_function=len,
                separators=["\n\n", "\n", ". ", " ", ""]
            )
        elif strategy == "token":
            splitter = TokenTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
        elif strategy == "semantic":
            if SemanticChunker is None:
                raise ImportError(
                    "SemanticChunker not available. Install with: "
                    "pip install langchain-experimental"
                )
            if embedding_model is None:
                raise ValueError("embedding_model is required for semantic chunking")

            splitter = SemanticChunker(embedding_model)
        else:
            raise ValueError(
                f"Invalid chunking strategy: {strategy}. "
                f"Must be one of: recursive, token, semantic"
            )

        # Split text
        text_chunks = splitter.split_text(text)

        # Create DocumentChunk objects
        chunks = []
        current_pos = 0

        for idx, chunk_text in enumerate(text_chunks):
            # Find chunk position in original text
            start_char = text.find(chunk_text, current_pos)
            if start_char == -1:
                start_char = current_pos
            end_char = start_char + len(chunk_text)
            current_pos = end_char

            # Generate chunk ID
            chunk_id = f"{document_id}_chunk_{idx}"

            # Create chunk
            chunk = DocumentChunk(
                chunk_id=chunk_id,
                document_id=document_id,
                text=chunk_text,
                metadata={
                    "strategy": strategy,
                    "chunk_size": chunk_size,
                    "chunk_overlap": chunk_overlap
                },
                chunk_index=idx,
                start_char=start_char,
                end_char=end_char
            )
            chunks.append(chunk)

        return chunks

    def extract_metadata(
        self,
        file_path: str,
        file_type: str
    ) -> Dict[str, Any]:
        """Extract metadata from document.

        Args:
            file_path: Path to document
            file_type: Type of document

        Returns:
            Dictionary of metadata
        """
        metadata = {
            "file_type": file_type,
            "file_size": os.path.getsize(file_path),
            "created_at": datetime.now().isoformat()
        }

        # PDF-specific metadata
        if file_type == "pdf" and PyPDF2:
            try:
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    metadata["num_pages"] = len(pdf_reader.pages)

                    if pdf_reader.metadata:
                        pdf_meta = pdf_reader.metadata
                        metadata["title"] = getattr(pdf_meta, 'title', None)
                        metadata["author"] = getattr(pdf_meta, 'author', None)
                        metadata["subject"] = getattr(pdf_meta, 'subject', None)
                        metadata["creator"] = getattr(pdf_meta, 'creator', None)
            except Exception:
                pass  # Fail silently for metadata extraction

        # DOCX-specific metadata
        elif file_type == "docx" and DocxDocument:
            try:
                doc = DocxDocument(file_path)
                core_props = doc.core_properties
                metadata["title"] = core_props.title
                metadata["author"] = core_props.author
                metadata["subject"] = core_props.subject
                metadata["created"] = core_props.created
                metadata["modified"] = core_props.modified
            except Exception:
                pass  # Fail silently for metadata extraction

        return metadata

    async def delete_document(
        self,
        document_id: str,
        file_path: str
    ) -> bool:
        """Delete a document and its associated file.

        Args:
            document_id: ID of document to delete
            file_path: Path to document file

        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete file if it exists
            path = Path(file_path)
            if path.exists():
                path.unlink()

            return True
        except Exception as e:
            # Log error but don't raise
            print(f"Error deleting document {document_id}: {str(e)}")
            return False

    def _detect_file_type(self, filename: str) -> str:
        """Detect file type from filename extension.

        Args:
            filename: Name of file

        Returns:
            File type (pdf, docx, txt, md)

        Raises:
            ValueError: If file type not supported
        """
        extension = filename.lower().split('.')[-1]

        if extension not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported file type: .{extension}. "
                f"Supported types: {', '.join(self.SUPPORTED_FORMATS.keys())}"
            )

        return extension

    def _generate_document_id(self, filename: str, file_data: bytes) -> str:
        """Generate unique document ID.

        Args:
            filename: Original filename
            file_data: File contents

        Returns:
            Unique document ID
        """
        # Create hash from filename and first 1KB of file
        hasher = hashlib.sha256()
        hasher.update(filename.encode('utf-8'))
        hasher.update(file_data[:1024])
        hasher.update(str(datetime.now().timestamp()).encode('utf-8'))

        return hasher.hexdigest()[:16]

    def get_supported_formats(self) -> List[str]:
        """Get list of supported file formats.

        Returns:
            List of supported extensions
        """
        return list(self.SUPPORTED_FORMATS.keys())
