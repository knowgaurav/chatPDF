"""
Text processing utilities for the chatPDF system.

This module provides:
- Text cleaning and normalization
- Whitespace handling
- Special character processing
- Text chunking helpers
- Token counting for different models
- Metadata extraction from text
"""

import re
import unicodedata
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import tiktoken

try:
    # Try new import path (langchain 0.2+)
    from langchain_text_splitters import (
        RecursiveCharacterTextSplitter,
        TokenTextSplitter,
        MarkdownHeaderTextSplitter
    )
except ImportError:
    # Fallback to old import path (langchain 0.1)
    from langchain.text_splitter import (
        RecursiveCharacterTextSplitter,
        TokenTextSplitter,
        MarkdownHeaderTextSplitter
    )


@dataclass
class TextChunk:
    """
    Represents a chunk of text with metadata.

    Attributes:
        text: The chunk text content
        chunk_id: Unique chunk identifier
        start_char: Starting character position in original text
        end_char: Ending character position in original text
        metadata: Additional metadata (page number, section, etc.)
        token_count: Number of tokens in the chunk
    """
    text: str
    chunk_id: int
    start_char: int
    end_char: int
    metadata: Dict[str, any]
    token_count: Optional[int] = None


class TextCleaner:
    """
    Provides text cleaning and normalization functions.
    """

    @staticmethod
    def clean_text(text: str, aggressive: bool = False) -> str:
        """
        Clean and normalize text.

        Args:
            text: Input text to clean
            aggressive: Whether to apply aggressive cleaning

        Returns:
            Cleaned text
        """
        if not text:
            return ""

        # Normalize unicode characters
        text = unicodedata.normalize('NFKC', text)

        # Remove null bytes
        text = text.replace('\x00', '')

        # Normalize whitespace
        text = TextCleaner.normalize_whitespace(text)

        if aggressive:
            # Remove special characters (keep alphanumeric, basic punctuation, whitespace)
            text = re.sub(r'[^\w\s\.,!?;:\-\(\)\[\]\"\']+', '', text)

            # Remove excessive punctuation
            text = re.sub(r'([!?.]){3,}', r'\1\1', text)

        # Remove leading/trailing whitespace
        text = text.strip()

        return text

    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """
        Normalize whitespace in text.

        - Replaces tabs with spaces
        - Removes excessive spaces
        - Normalizes line breaks
        - Removes trailing whitespace from lines

        Args:
            text: Input text

        Returns:
            Text with normalized whitespace
        """
        if not text:
            return ""

        # Replace tabs with spaces
        text = text.replace('\t', ' ')

        # Normalize line breaks (convert \r\n and \r to \n)
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        # Remove trailing whitespace from each line
        lines = text.split('\n')
        lines = [line.rstrip() for line in lines]

        # Join lines back
        text = '\n'.join(lines)

        # Remove excessive blank lines (more than 2 consecutive)
        text = re.sub(r'\n{3,}', '\n\n', text)

        # Remove excessive spaces (but keep paragraph breaks)
        text = re.sub(r' {2,}', ' ', text)

        return text

    @staticmethod
    def remove_urls(text: str) -> str:
        """
        Remove URLs from text.

        Args:
            text: Input text

        Returns:
            Text with URLs removed
        """
        # Remove URLs
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        text = re.sub(url_pattern, '', text)

        return text

    @staticmethod
    def remove_emails(text: str) -> str:
        """
        Remove email addresses from text.

        Args:
            text: Input text

        Returns:
            Text with emails removed
        """
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        text = re.sub(email_pattern, '', text)

        return text

    @staticmethod
    def remove_phone_numbers(text: str) -> str:
        """
        Remove phone numbers from text.

        Args:
            text: Input text

        Returns:
            Text with phone numbers removed
        """
        # Match common phone number formats
        phone_patterns = [
            r'\+?1?\d{9,15}',  # International format
            r'\(\d{3}\)\s*\d{3}[-.\s]?\d{4}',  # (123) 456-7890
            r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',  # 123-456-7890
        ]

        for pattern in phone_patterns:
            text = re.sub(pattern, '', text)

        return text

    @staticmethod
    def extract_sentences(text: str) -> List[str]:
        """
        Extract sentences from text.

        Args:
            text: Input text

        Returns:
            List of sentences
        """
        # Simple sentence splitting (can be improved with NLTK or spaCy)
        sentence_pattern = r'[.!?]+[\s]+'
        sentences = re.split(sentence_pattern, text)

        # Clean and filter empty sentences
        sentences = [s.strip() for s in sentences if s.strip()]

        return sentences

    @staticmethod
    def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
        """
        Truncate text to maximum length.

        Args:
            text: Input text
            max_length: Maximum length
            suffix: Suffix to add if truncated

        Returns:
            Truncated text
        """
        if len(text) <= max_length:
            return text

        return text[:max_length - len(suffix)] + suffix


class TokenCounter:
    """
    Token counting utilities for different models.
    """

    # Model encoding mappings
    MODEL_ENCODINGS = {
        'gpt-4': 'cl100k_base',
        'gpt-4-32k': 'cl100k_base',
        'gpt-3.5-turbo': 'cl100k_base',
        'gpt-3.5-turbo-16k': 'cl100k_base',
        'text-embedding-ada-002': 'cl100k_base',
        'text-davinci-003': 'p50k_base',
        'text-davinci-002': 'p50k_base',
        'code-davinci-002': 'p50k_base',
    }

    def __init__(self, model: str = 'gpt-3.5-turbo'):
        """
        Initialize token counter for a specific model.

        Args:
            model: Model name
        """
        self.model = model
        self.encoding_name = self.MODEL_ENCODINGS.get(model, 'cl100k_base')
        self.encoding = tiktoken.get_encoding(self.encoding_name)

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.

        Args:
            text: Input text

        Returns:
            Number of tokens
        """
        if not text:
            return 0

        return len(self.encoding.encode(text))

    def count_tokens_batch(self, texts: List[str]) -> List[int]:
        """
        Count tokens for multiple texts.

        Args:
            texts: List of texts

        Returns:
            List of token counts
        """
        return [self.count_tokens(text) for text in texts]

    def truncate_to_token_limit(self, text: str, max_tokens: int) -> str:
        """
        Truncate text to fit within token limit.

        Args:
            text: Input text
            max_tokens: Maximum number of tokens

        Returns:
            Truncated text
        """
        if not text:
            return ""

        tokens = self.encoding.encode(text)

        if len(tokens) <= max_tokens:
            return text

        # Truncate tokens and decode back to text
        truncated_tokens = tokens[:max_tokens]
        return self.encoding.decode(truncated_tokens)

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """
        Estimate token count without encoding (faster but less accurate).

        Uses approximation: ~4 characters per token for English text.

        Args:
            text: Input text

        Returns:
            Estimated token count
        """
        return len(text) // 4


class TextChunker:
    """
    Text chunking utilities with various strategies.
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        model: str = 'gpt-3.5-turbo'
    ):
        """
        Initialize text chunker.

        Args:
            chunk_size: Target chunk size (in characters or tokens)
            chunk_overlap: Overlap between chunks
            model: Model for token counting
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.model = model
        self.token_counter = TokenCounter(model)

    def chunk_by_characters(
        self,
        text: str,
        separators: Optional[List[str]] = None,
        metadata: Optional[Dict] = None
    ) -> List[TextChunk]:
        """
        Chunk text by characters using recursive splitting.

        Args:
            text: Input text
            separators: List of separators to use for splitting
            metadata: Base metadata to add to all chunks

        Returns:
            List of TextChunk objects
        """
        if separators is None:
            separators = ["\n\n", "\n", ". ", " ", ""]

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=separators,
            length_function=len
        )

        chunks = splitter.split_text(text)
        return self._create_chunks(chunks, text, metadata or {})

    def chunk_by_tokens(
        self,
        text: str,
        metadata: Optional[Dict] = None
    ) -> List[TextChunk]:
        """
        Chunk text by token count.

        Args:
            text: Input text
            metadata: Base metadata to add to all chunks

        Returns:
            List of TextChunk objects
        """
        splitter = TokenTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            encoding_name=self.token_counter.encoding_name
        )

        chunks = splitter.split_text(text)
        return self._create_chunks(chunks, text, metadata or {})

    def chunk_by_sentences(
        self,
        text: str,
        metadata: Optional[Dict] = None
    ) -> List[TextChunk]:
        """
        Chunk text by sentences.

        Args:
            text: Input text
            metadata: Base metadata to add to all chunks

        Returns:
            List of TextChunk objects
        """
        sentences = TextCleaner.extract_sentences(text)
        chunks = []
        current_chunk = []
        current_length = 0

        for sentence in sentences:
            sentence_length = len(sentence)

            if current_length + sentence_length > self.chunk_size and current_chunk:
                # Save current chunk
                chunk_text = ' '.join(current_chunk)
                chunks.append(chunk_text)

                # Start new chunk with overlap
                overlap_sentences = current_chunk[-2:] if len(current_chunk) >= 2 else current_chunk
                current_chunk = overlap_sentences + [sentence]
                current_length = sum(len(s) for s in current_chunk)
            else:
                current_chunk.append(sentence)
                current_length += sentence_length

        # Add final chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return self._create_chunks(chunks, text, metadata or {})

    def chunk_markdown(
        self,
        text: str,
        headers_to_split_on: Optional[List[Tuple[str, str]]] = None,
        metadata: Optional[Dict] = None
    ) -> List[TextChunk]:
        """
        Chunk markdown text preserving structure.

        Args:
            text: Markdown text
            headers_to_split_on: List of (header, name) tuples
            metadata: Base metadata to add to all chunks

        Returns:
            List of TextChunk objects
        """
        if headers_to_split_on is None:
            headers_to_split_on = [
                ("#", "h1"),
                ("##", "h2"),
                ("###", "h3"),
            ]

        splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=headers_to_split_on
        )

        chunks = splitter.split_text(text)

        # Convert to TextChunk objects
        text_chunks = []
        for i, chunk in enumerate(chunks):
            chunk_metadata = metadata.copy() if metadata else {}
            chunk_metadata.update(chunk.metadata)

            text_chunks.append(TextChunk(
                text=chunk.page_content,
                chunk_id=i,
                start_char=0,  # Not tracked for markdown
                end_char=len(chunk.page_content),
                metadata=chunk_metadata,
                token_count=self.token_counter.count_tokens(chunk.page_content)
            ))

        return text_chunks

    def _create_chunks(
        self,
        chunk_texts: List[str],
        original_text: str,
        base_metadata: Dict
    ) -> List[TextChunk]:
        """
        Create TextChunk objects from chunk texts.

        Args:
            chunk_texts: List of chunk text strings
            original_text: Original full text
            base_metadata: Base metadata for all chunks

        Returns:
            List of TextChunk objects
        """
        chunks = []
        current_pos = 0

        for i, chunk_text in enumerate(chunk_texts):
            # Find chunk position in original text
            start_pos = original_text.find(chunk_text, current_pos)
            if start_pos == -1:
                start_pos = current_pos

            end_pos = start_pos + len(chunk_text)

            # Create chunk
            chunk = TextChunk(
                text=chunk_text,
                chunk_id=i,
                start_char=start_pos,
                end_char=end_pos,
                metadata=base_metadata.copy(),
                token_count=self.token_counter.count_tokens(chunk_text)
            )

            chunks.append(chunk)
            current_pos = end_pos

        return chunks


class MetadataExtractor:
    """
    Extract metadata from text.
    """

    @staticmethod
    def extract_title(text: str) -> Optional[str]:
        """
        Extract title from text (first line or heading).

        Args:
            text: Input text

        Returns:
            Extracted title or None
        """
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if line:
                # Check if it's a markdown heading
                if line.startswith('#'):
                    return line.lstrip('#').strip()
                # Otherwise return first non-empty line
                return line[:100]  # Limit title length

        return None

    @staticmethod
    def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
        """
        Extract keywords from text (simple frequency-based).

        Args:
            text: Input text
            max_keywords: Maximum number of keywords to extract

        Returns:
            List of keywords
        """
        # Simple word frequency approach
        # For better results, use TF-IDF or NLP libraries

        # Remove common words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
            'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these',
            'those', 'it', 'its', 'they', 'them', 'their'
        }

        # Extract words
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())

        # Filter stop words and count frequency
        word_freq = {}
        for word in words:
            if word not in stop_words:
                word_freq[word] = word_freq.get(word, 0) + 1

        # Sort by frequency and return top keywords
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        keywords = [word for word, freq in sorted_words[:max_keywords]]

        return keywords

    @staticmethod
    def extract_summary(text: str, max_sentences: int = 3) -> str:
        """
        Extract a simple summary (first N sentences).

        Args:
            text: Input text
            max_sentences: Maximum number of sentences

        Returns:
            Summary text
        """
        sentences = TextCleaner.extract_sentences(text)

        if not sentences:
            return ""

        summary_sentences = sentences[:max_sentences]
        return ' '.join(summary_sentences)


# Example usage
if __name__ == "__main__":
    # Test text cleaning
    sample_text = """
    This    is   a    sample   text    with    extra     spaces.

    It also has  multiple   blank lines.


    And some URLs: https://example.com
    """

    cleaner = TextCleaner()
    cleaned = cleaner.clean_text(sample_text)
    print("Cleaned text:", cleaned)

    # Test token counting
    counter = TokenCounter()
    tokens = counter.count_tokens(cleaned)
    print(f"Token count: {tokens}")

    # Test chunking
    chunker = TextChunker(chunk_size=50, chunk_overlap=10)
    chunks = chunker.chunk_by_characters(cleaned)
    print(f"Number of chunks: {len(chunks)}")
    for chunk in chunks:
        print(f"Chunk {chunk.chunk_id}: {chunk.text[:50]}... ({chunk.token_count} tokens)")
