"""
Logging configuration for the chatPDF system.

This module provides:
- Python logging configuration
- File and console handlers with rotation
- Different log levels for different components
- Structured logging for RAG pipeline steps
- Cost and latency tracking
- Performance monitoring
"""

import logging
import logging.handlers
import sys
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from functools import wraps
import time


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter for structured logging.

    Adds JSON-formatted metadata to log records for better parsing and analysis.
    """

    def __init__(self, include_extras: bool = True):
        """
        Initialize the structured formatter.

        Args:
            include_extras: Whether to include extra fields in the log output
        """
        super().__init__()
        self.include_extras = include_extras

    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record with structured data.

        Args:
            record: The log record to format

        Returns:
            Formatted log string
        """
        # Base log message
        timestamp = datetime.fromtimestamp(record.created).isoformat()
        base_message = f"[{timestamp}] [{record.levelname}] [{record.name}] {record.getMessage()}"

        # Add extra fields if available
        if self.include_extras and hasattr(record, 'extras'):
            extras = getattr(record, 'extras')
            if extras:
                extras_str = json.dumps(extras, default=str)
                base_message += f" | {extras_str}"

        # Add exception info if present
        if record.exc_info:
            base_message += "\n" + self.formatException(record.exc_info)

        return base_message


class RAGPipelineLogger:
    """
    Specialized logger for RAG pipeline steps.

    Provides structured logging for:
    - Document processing
    - Query processing
    - Retrieval steps
    - LLM generation
    - Cost tracking
    """

    def __init__(self, logger: logging.Logger):
        """
        Initialize the RAG pipeline logger.

        Args:
            logger: Base logger instance
        """
        self.logger = logger

    def log_document_processing(
        self,
        document_id: str,
        filename: str,
        file_size: int,
        num_chunks: int,
        processing_time_ms: float,
        embedding_model: str
    ):
        """
        Log document processing details.

        Args:
            document_id: Unique document identifier
            filename: Document filename
            file_size: File size in bytes
            num_chunks: Number of chunks created
            processing_time_ms: Processing time in milliseconds
            embedding_model: Embedding model used
        """
        self.logger.info(
            f"Document processed: {filename}",
            extra={
                'extras': {
                    'document_id': document_id,
                    'filename': filename,
                    'file_size': file_size,
                    'num_chunks': num_chunks,
                    'processing_time_ms': processing_time_ms,
                    'embedding_model': embedding_model,
                    'event_type': 'document_processing'
                }
            }
        )

    def log_query_start(
        self,
        query_id: str,
        query: str,
        document_ids: list,
        rag_strategy: str
    ):
        """
        Log query start.

        Args:
            query_id: Unique query identifier
            query: User query text
            document_ids: List of document IDs to search
            rag_strategy: RAG strategy being used
        """
        self.logger.info(
            f"Query started: {query[:100]}...",
            extra={
                'extras': {
                    'query_id': query_id,
                    'query': query,
                    'document_ids': document_ids,
                    'rag_strategy': rag_strategy,
                    'event_type': 'query_start'
                }
            }
        )

    def log_retrieval_step(
        self,
        query_id: str,
        step_name: str,
        num_results: int,
        latency_ms: float,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log a retrieval pipeline step.

        Args:
            query_id: Unique query identifier
            step_name: Name of the retrieval step (e.g., 'semantic_search', 'reranking')
            num_results: Number of results retrieved
            latency_ms: Step latency in milliseconds
            metadata: Additional metadata
        """
        extras = {
            'query_id': query_id,
            'step_name': step_name,
            'num_results': num_results,
            'latency_ms': latency_ms,
            'event_type': 'retrieval_step'
        }
        if metadata:
            extras.update(metadata)

        self.logger.debug(
            f"Retrieval step '{step_name}' completed: {num_results} results in {latency_ms:.2f}ms",
            extra={'extras': extras}
        )

    def log_llm_generation(
        self,
        query_id: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        cost: float,
        latency_ms: float,
        streaming: bool = False
    ):
        """
        Log LLM generation details.

        Args:
            query_id: Unique query identifier
            model: LLM model name
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            total_tokens: Total tokens used
            cost: API cost in USD
            latency_ms: Generation latency in milliseconds
            streaming: Whether streaming was used
        """
        self.logger.info(
            f"LLM generation completed: {model} ({total_tokens} tokens, ${cost:.4f})",
            extra={
                'extras': {
                    'query_id': query_id,
                    'model': model,
                    'prompt_tokens': prompt_tokens,
                    'completion_tokens': completion_tokens,
                    'total_tokens': total_tokens,
                    'cost_usd': cost,
                    'latency_ms': latency_ms,
                    'streaming': streaming,
                    'event_type': 'llm_generation'
                }
            }
        )

    def log_query_complete(
        self,
        query_id: str,
        total_latency_ms: float,
        total_tokens: int,
        total_cost: float,
        num_sources: int,
        success: bool = True,
        error: Optional[str] = None
    ):
        """
        Log query completion.

        Args:
            query_id: Unique query identifier
            total_latency_ms: Total query latency in milliseconds
            total_tokens: Total tokens used
            total_cost: Total cost in USD
            num_sources: Number of sources cited
            success: Whether the query succeeded
            error: Error message if failed
        """
        level = logging.INFO if success else logging.ERROR
        message = f"Query completed: {total_latency_ms:.2f}ms, {total_tokens} tokens, ${total_cost:.4f}"

        if not success and error:
            message = f"Query failed: {error}"

        self.logger.log(
            level,
            message,
            extra={
                'extras': {
                    'query_id': query_id,
                    'total_latency_ms': total_latency_ms,
                    'total_tokens': total_tokens,
                    'total_cost_usd': total_cost,
                    'num_sources': num_sources,
                    'success': success,
                    'error': error,
                    'event_type': 'query_complete'
                }
            }
        )


def setup_logging(
    log_level: str = "INFO",
    log_dir: str = "logs",
    log_file: str = "chatpdf.log",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    console_output: bool = True,
    structured_format: bool = True
) -> None:
    """
    Set up application-wide logging configuration.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files
        log_file: Log filename
        max_bytes: Maximum log file size before rotation
        backup_count: Number of backup files to keep
        console_output: Whether to output logs to console
        structured_format: Whether to use structured formatting
    """
    # Create log directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    root_logger.handlers.clear()

    # Create formatter
    if structured_format:
        formatter = StructuredFormatter(include_extras=True)
    else:
        formatter = logging.Formatter(
            fmt='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_path / log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # Set specific log levels for different components
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('openai').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)

    root_logger.info(f"Logging initialized: level={log_level}, file={log_path / log_file}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the specified module.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def get_rag_logger(name: str) -> RAGPipelineLogger:
    """
    Get a RAG pipeline logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        RAGPipelineLogger instance
    """
    logger = logging.getLogger(name)
    return RAGPipelineLogger(logger)


def log_execution_time(logger: Optional[logging.Logger] = None):
    """
    Decorator to log function execution time.

    Args:
        logger: Logger instance (uses root logger if None)

    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            _logger = logger or logging.getLogger(func.__module__)
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                execution_time = (time.time() - start_time) * 1000  # Convert to ms

                _logger.debug(
                    f"{func.__name__} executed in {execution_time:.2f}ms",
                    extra={
                        'extras': {
                            'function': func.__name__,
                            'execution_time_ms': execution_time,
                            'event_type': 'function_execution'
                        }
                    }
                )

                return result
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                _logger.error(
                    f"{func.__name__} failed after {execution_time:.2f}ms: {str(e)}",
                    extra={
                        'extras': {
                            'function': func.__name__,
                            'execution_time_ms': execution_time,
                            'error': str(e),
                            'event_type': 'function_error'
                        }
                    },
                    exc_info=True
                )
                raise

        return wrapper
    return decorator


def log_async_execution_time(logger: Optional[logging.Logger] = None):
    """
    Decorator to log async function execution time.

    Args:
        logger: Logger instance (uses root logger if None)

    Returns:
        Decorated async function
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            _logger = logger or logging.getLogger(func.__module__)
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)
                execution_time = (time.time() - start_time) * 1000  # Convert to ms

                _logger.debug(
                    f"{func.__name__} executed in {execution_time:.2f}ms",
                    extra={
                        'extras': {
                            'function': func.__name__,
                            'execution_time_ms': execution_time,
                            'event_type': 'async_function_execution'
                        }
                    }
                )

                return result
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                _logger.error(
                    f"{func.__name__} failed after {execution_time:.2f}ms: {str(e)}",
                    extra={
                        'extras': {
                            'function': func.__name__,
                            'execution_time_ms': execution_time,
                            'error': str(e),
                            'event_type': 'async_function_error'
                        }
                    },
                    exc_info=True
                )
                raise

        return wrapper
    return decorator


# Example usage
if __name__ == "__main__":
    # Set up logging
    setup_logging(log_level="DEBUG", log_dir="logs")

    # Get logger
    logger = get_logger(__name__)
    logger.info("Logger test message")

    # Get RAG logger
    rag_logger = get_rag_logger(__name__)
    rag_logger.log_query_start(
        query_id="test-123",
        query="What is this document about?",
        document_ids=["doc-1", "doc-2"],
        rag_strategy="hybrid"
    )

    # Test execution time decorator
    @log_execution_time(logger)
    def example_function():
        time.sleep(0.1)
        return "Done"

    example_function()
