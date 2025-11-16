"""
Input validation utilities for the chatPDF system.

This module provides:
- File type validation
- File size validation
- Query validation
- Configuration validation
- Sanitization helpers
- Custom validation exceptions
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass


class ValidationError(Exception):
    """Custom exception for validation errors."""

    def __init__(self, message: str, field: Optional[str] = None):
        """
        Initialize validation error.

        Args:
            message: Error message
            field: Field name that failed validation
        """
        self.message = message
        self.field = field
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for API responses."""
        return {
            'error': 'ValidationError',
            'message': self.message,
            'field': self.field
        }


@dataclass
class FileValidationResult:
    """
    Result of file validation.

    Attributes:
        is_valid: Whether the file is valid
        errors: List of validation errors
        warnings: List of validation warnings
        metadata: Additional metadata about the file
    """
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]


class FileValidator:
    """
    Validates uploaded files.
    """

    # Default allowed file types
    ALLOWED_EXTENSIONS = {
        'pdf': ['application/pdf'],
        'docx': [
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        ],
        'doc': ['application/msword'],
        'txt': ['text/plain'],
        'md': ['text/markdown', 'text/plain'],
        'csv': ['text/csv'],
    }

    # Maximum file size (50 MB)
    MAX_FILE_SIZE = 50 * 1024 * 1024  # bytes

    # Minimum file size (1 KB)
    MIN_FILE_SIZE = 1024  # bytes

    @classmethod
    def validate_file_type(
        cls,
        filename: str,
        allowed_extensions: Optional[List[str]] = None
    ) -> bool:
        """
        Validate file type by extension.

        Args:
            filename: Name of the file
            allowed_extensions: List of allowed extensions (uses default if None)

        Returns:
            True if file type is valid

        Raises:
            ValidationError: If file type is invalid
        """
        if not filename:
            raise ValidationError("Filename is required", field="filename")

        # Get file extension
        file_ext = Path(filename).suffix.lower().lstrip('.')

        # Use default allowed extensions if not provided
        if allowed_extensions is None:
            allowed_extensions = list(cls.ALLOWED_EXTENSIONS.keys())

        if file_ext not in allowed_extensions:
            raise ValidationError(
                f"File type '.{file_ext}' not allowed. Allowed types: {', '.join(allowed_extensions)}",
                field="file_type"
            )

        return True

    @classmethod
    def validate_file_size(
        cls,
        file_size: int,
        max_size: Optional[int] = None,
        min_size: Optional[int] = None
    ) -> bool:
        """
        Validate file size.

        Args:
            file_size: File size in bytes
            max_size: Maximum allowed size (uses default if None)
            min_size: Minimum allowed size (uses default if None)

        Returns:
            True if file size is valid

        Raises:
            ValidationError: If file size is invalid
        """
        max_size = max_size or cls.MAX_FILE_SIZE
        min_size = min_size or cls.MIN_FILE_SIZE

        if file_size > max_size:
            max_mb = max_size / (1024 * 1024)
            raise ValidationError(
                f"File size ({file_size / (1024 * 1024):.2f} MB) exceeds maximum allowed size ({max_mb:.2f} MB)",
                field="file_size"
            )

        if file_size < min_size:
            raise ValidationError(
                f"File size ({file_size} bytes) is below minimum required size ({min_size} bytes)",
                field="file_size"
            )

        return True

    @classmethod
    def validate_file(
        cls,
        file_path: str,
        allowed_extensions: Optional[List[str]] = None,
        max_size: Optional[int] = None,
        min_size: Optional[int] = None
    ) -> FileValidationResult:
        """
        Comprehensive file validation.

        Args:
            file_path: Path to the file
            allowed_extensions: List of allowed extensions
            max_size: Maximum file size
            min_size: Minimum file size

        Returns:
            FileValidationResult with validation details
        """
        errors = []
        warnings = []
        metadata = {}

        # Check if file exists
        if not os.path.exists(file_path):
            errors.append(f"File not found: {file_path}")
            return FileValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                metadata=metadata
            )

        # Get file metadata
        file_stat = os.stat(file_path)
        file_size = file_stat.st_size
        filename = os.path.basename(file_path)

        metadata['filename'] = filename
        metadata['file_size'] = file_size
        metadata['file_path'] = file_path

        # Validate file type
        try:
            cls.validate_file_type(filename, allowed_extensions)
        except ValidationError as e:
            errors.append(e.message)

        # Validate file size
        try:
            cls.validate_file_size(file_size, max_size, min_size)
        except ValidationError as e:
            errors.append(e.message)

        # Check if file is readable
        if not os.access(file_path, os.R_OK):
            errors.append("File is not readable")

        # Check if file is empty
        if file_size == 0:
            errors.append("File is empty")

        # Warnings for large files
        if file_size > 10 * 1024 * 1024:  # 10 MB
            warnings.append("File is large and may take longer to process")

        is_valid = len(errors) == 0

        return FileValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            metadata=metadata
        )


class QueryValidator:
    """
    Validates user queries and search parameters.
    """

    # Query constraints
    MIN_QUERY_LENGTH = 3
    MAX_QUERY_LENGTH = 1000

    # Forbidden patterns (potential injection attacks)
    FORBIDDEN_PATTERNS = [
        r'<script[^>]*>.*?</script>',  # Script tags
        r'javascript:',  # JavaScript protocol
        r'on\w+\s*=',  # Event handlers
    ]

    @classmethod
    def validate_query(
        cls,
        query: str,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None
    ) -> bool:
        """
        Validate user query.

        Args:
            query: User query string
            min_length: Minimum query length
            max_length: Maximum query length

        Returns:
            True if query is valid

        Raises:
            ValidationError: If query is invalid
        """
        if not query:
            raise ValidationError("Query is required", field="query")

        # Strip whitespace
        query = query.strip()

        # Check length
        min_len = min_length or cls.MIN_QUERY_LENGTH
        max_len = max_length or cls.MAX_QUERY_LENGTH

        if len(query) < min_len:
            raise ValidationError(
                f"Query is too short (minimum {min_len} characters)",
                field="query"
            )

        if len(query) > max_len:
            raise ValidationError(
                f"Query is too long (maximum {max_len} characters)",
                field="query"
            )

        # Check for forbidden patterns
        for pattern in cls.FORBIDDEN_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                raise ValidationError(
                    "Query contains forbidden content",
                    field="query"
                )

        return True

    @classmethod
    def validate_top_k(cls, top_k: int) -> bool:
        """
        Validate top_k parameter.

        Args:
            top_k: Number of results to retrieve

        Returns:
            True if valid

        Raises:
            ValidationError: If invalid
        """
        if top_k < 1:
            raise ValidationError(
                "top_k must be at least 1",
                field="top_k"
            )

        if top_k > 100:
            raise ValidationError(
                "top_k cannot exceed 100",
                field="top_k"
            )

        return True

    @classmethod
    def validate_temperature(cls, temperature: float) -> bool:
        """
        Validate temperature parameter.

        Args:
            temperature: LLM temperature

        Returns:
            True if valid

        Raises:
            ValidationError: If invalid
        """
        if temperature < 0.0 or temperature > 2.0:
            raise ValidationError(
                "temperature must be between 0.0 and 2.0",
                field="temperature"
            )

        return True

    @classmethod
    def validate_max_tokens(cls, max_tokens: int) -> bool:
        """
        Validate max_tokens parameter.

        Args:
            max_tokens: Maximum tokens to generate

        Returns:
            True if valid

        Raises:
            ValidationError: If invalid
        """
        if max_tokens < 1:
            raise ValidationError(
                "max_tokens must be at least 1",
                field="max_tokens"
            )

        if max_tokens > 4096:
            raise ValidationError(
                "max_tokens cannot exceed 4096",
                field="max_tokens"
            )

        return True


class ConfigValidator:
    """
    Validates configuration settings.
    """

    VALID_MODELS = [
        'gpt-4',
        'gpt-4-turbo',
        'gpt-3.5-turbo',
        'gpt-3.5-turbo-16k',
        'llama3:8b',
        'llama3:70b',
        'mistral:7b',
        'mistral:latest',
    ]

    VALID_EMBEDDING_MODELS = [
        'text-embedding-ada-002',
        'text-embedding-3-small',
        'text-embedding-3-large',
        'all-MiniLM-L6-v2',
        'all-mpnet-base-v2',
        'bge-small-en-v1.5',
    ]

    VALID_RAG_STRATEGIES = [
        'semantic',
        'keyword',
        'hybrid',
        'multi-query',
        're-ranked',
    ]

    VALID_CHUNKING_STRATEGIES = [
        'recursive',
        'token',
        'sentence',
        'markdown',
    ]

    @classmethod
    def validate_model(cls, model: str) -> bool:
        """
        Validate model name.

        Args:
            model: Model name

        Returns:
            True if valid

        Raises:
            ValidationError: If invalid
        """
        if not model:
            raise ValidationError("Model is required", field="model")

        # Allow any model that starts with a known prefix
        valid_prefixes = ['gpt-', 'llama', 'mistral', 'claude']

        if model in cls.VALID_MODELS:
            return True

        if any(model.startswith(prefix) for prefix in valid_prefixes):
            return True

        raise ValidationError(
            f"Invalid model: {model}",
            field="model"
        )

    @classmethod
    def validate_embedding_model(cls, model: str) -> bool:
        """
        Validate embedding model name.

        Args:
            model: Embedding model name

        Returns:
            True if valid

        Raises:
            ValidationError: If invalid
        """
        if not model:
            raise ValidationError(
                "Embedding model is required",
                field="embedding_model"
            )

        if model not in cls.VALID_EMBEDDING_MODELS:
            raise ValidationError(
                f"Invalid embedding model: {model}. Valid models: {', '.join(cls.VALID_EMBEDDING_MODELS)}",
                field="embedding_model"
            )

        return True

    @classmethod
    def validate_rag_strategy(cls, strategy: str) -> bool:
        """
        Validate RAG strategy.

        Args:
            strategy: RAG strategy name

        Returns:
            True if valid

        Raises:
            ValidationError: If invalid
        """
        if strategy not in cls.VALID_RAG_STRATEGIES:
            raise ValidationError(
                f"Invalid RAG strategy: {strategy}. Valid strategies: {', '.join(cls.VALID_RAG_STRATEGIES)}",
                field="rag_strategy"
            )

        return True

    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> bool:
        """
        Validate complete configuration.

        Args:
            config: Configuration dictionary

        Returns:
            True if valid

        Raises:
            ValidationError: If invalid
        """
        # Validate model if present
        if 'model' in config:
            cls.validate_model(config['model'])

        # Validate embedding model if present
        if 'embedding_model' in config:
            cls.validate_embedding_model(config['embedding_model'])

        # Validate RAG strategy if present
        if 'rag_strategy' in config:
            cls.validate_rag_strategy(config['rag_strategy'])

        # Validate temperature if present
        if 'temperature' in config:
            QueryValidator.validate_temperature(config['temperature'])

        # Validate max_tokens if present
        if 'max_tokens' in config:
            QueryValidator.validate_max_tokens(config['max_tokens'])

        # Validate top_k if present
        if 'top_k' in config:
            QueryValidator.validate_top_k(config['top_k'])

        # Validate chunk_size if present
        if 'chunk_size' in config:
            chunk_size = config['chunk_size']
            if chunk_size < 100 or chunk_size > 5000:
                raise ValidationError(
                    "chunk_size must be between 100 and 5000",
                    field="chunk_size"
                )

        # Validate chunk_overlap if present
        if 'chunk_overlap' in config:
            overlap = config['chunk_overlap']
            if overlap < 0:
                raise ValidationError(
                    "chunk_overlap cannot be negative",
                    field="chunk_overlap"
                )

            if 'chunk_size' in config and overlap >= config['chunk_size']:
                raise ValidationError(
                    "chunk_overlap must be less than chunk_size",
                    field="chunk_overlap"
                )

        return True


class Sanitizer:
    """
    Sanitization utilities to clean user input.
    """

    @staticmethod
    def sanitize_input(text: str) -> str:
        """
        Sanitize user input to prevent injection attacks.

        Args:
            text: Input text

        Returns:
            Sanitized text
        """
        if not text:
            return ""

        # Remove null bytes
        text = text.replace('\x00', '')

        # Remove potential XSS patterns
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
        text = re.sub(r'on\w+\s*=', '', text, flags=re.IGNORECASE)

        # Remove SQL injection patterns
        text = re.sub(r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)', '', text, flags=re.IGNORECASE)

        return text.strip()

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename to prevent path traversal attacks.

        Args:
            filename: Original filename

        Returns:
            Sanitized filename
        """
        if not filename:
            return "untitled"

        # Get just the filename (no path)
        filename = os.path.basename(filename)

        # Remove dangerous characters
        filename = re.sub(r'[^\w\s\-\.]', '', filename)

        # Remove leading/trailing dots and spaces
        filename = filename.strip('. ')

        # Limit length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:250] + ext

        return filename or "untitled"

    @staticmethod
    def sanitize_path(path: str, base_dir: str) -> str:
        """
        Sanitize file path to prevent directory traversal.

        Args:
            path: Input path
            base_dir: Base directory (all paths must be within this)

        Returns:
            Sanitized absolute path

        Raises:
            ValidationError: If path is outside base directory
        """
        # Resolve to absolute paths
        base_dir = os.path.abspath(base_dir)
        abs_path = os.path.abspath(os.path.join(base_dir, path))

        # Check if path is within base_dir
        if not abs_path.startswith(base_dir):
            raise ValidationError(
                "Invalid path: outside base directory",
                field="path"
            )

        return abs_path


def validate_file_type(filename: str, allowed_extensions: Optional[List[str]] = None) -> bool:
    """Convenience function for file type validation."""
    return FileValidator.validate_file_type(filename, allowed_extensions)


def validate_file_size(file_size: int, max_size: Optional[int] = None) -> bool:
    """Convenience function for file size validation."""
    return FileValidator.validate_file_size(file_size, max_size)


def validate_query(query: str) -> bool:
    """Convenience function for query validation."""
    return QueryValidator.validate_query(query)


def validate_config(config: Dict[str, Any]) -> bool:
    """Convenience function for config validation."""
    return ConfigValidator.validate_config(config)


def sanitize_input(text: str) -> str:
    """Convenience function for input sanitization."""
    return Sanitizer.sanitize_input(text)


# Example usage
if __name__ == "__main__":
    # Test file validation
    try:
        validate_file_type("document.pdf")
        print("File type valid")
    except ValidationError as e:
        print(f"Validation error: {e.message}")

    # Test query validation
    try:
        validate_query("What is this document about?")
        print("Query valid")
    except ValidationError as e:
        print(f"Validation error: {e.message}")

    # Test config validation
    config = {
        'model': 'gpt-4',
        'temperature': 0.7,
        'top_k': 5
    }
    try:
        validate_config(config)
        print("Config valid")
    except ValidationError as e:
        print(f"Validation error: {e.message}")

    # Test sanitization
    dirty_input = "<script>alert('xss')</script>Hello"
    clean_input = sanitize_input(dirty_input)
    print(f"Sanitized: {clean_input}")
