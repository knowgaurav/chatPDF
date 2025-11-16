"""
Utility modules for the chatPDF system.

This package contains reusable utility functions and classes for:
- Logging and monitoring (logger.py)
- Text processing and chunking (text_processing.py)
- API cost tracking (cost_tracker.py)
- Input validation (validators.py)
- General helper functions (helpers.py)
"""

from .logger import (
    get_logger,
    get_rag_logger,
    setup_logging,
    RAGPipelineLogger,
    log_execution_time,
    log_async_execution_time
)

from .text_processing import (
    TextCleaner,
    TokenCounter,
    TextChunker,
    MetadataExtractor,
    TextChunk
)

from .cost_tracker import (
    CostTracker,
    UsageRecord,
    ModelPricing
)

from .validators import (
    ValidationError,
    FileValidator,
    QueryValidator,
    ConfigValidator,
    Sanitizer,
    validate_file_type,
    validate_file_size,
    validate_query,
    validate_config,
    sanitize_input
)

from .helpers import (
    DateTimeHelper,
    FileHelper,
    JSONHelper,
    ErrorFormatter,
    ResponseFormatter,
    CostFormatter,
    IDGenerator,
    format_datetime,
    format_file_size,
    format_cost,
    safe_json_dumps,
    safe_json_loads,
    format_error,
    ensure_directory,
    generate_uuid
)

__all__ = [
    # Logger
    "get_logger",
    "get_rag_logger",
    "setup_logging",
    "RAGPipelineLogger",
    "log_execution_time",
    "log_async_execution_time",
    # Text Processing
    "TextCleaner",
    "TokenCounter",
    "TextChunker",
    "MetadataExtractor",
    "TextChunk",
    # Cost Tracker
    "CostTracker",
    "UsageRecord",
    "ModelPricing",
    # Validators
    "ValidationError",
    "FileValidator",
    "QueryValidator",
    "ConfigValidator",
    "Sanitizer",
    "validate_file_type",
    "validate_file_size",
    "validate_query",
    "validate_config",
    "sanitize_input",
    # Helpers
    "DateTimeHelper",
    "FileHelper",
    "JSONHelper",
    "ErrorFormatter",
    "ResponseFormatter",
    "CostFormatter",
    "IDGenerator",
    "format_datetime",
    "format_file_size",
    "format_cost",
    "safe_json_dumps",
    "safe_json_loads",
    "format_error",
    "ensure_directory",
    "generate_uuid",
]
