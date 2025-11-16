# Utilities Quick Start Guide

## Import and Use

### 1. Logger - Get Started in 3 Lines

```python
from src.utils import setup_logging, get_logger

setup_logging(log_level="INFO", log_dir="logs")
logger = get_logger(__name__)
logger.info("Application started!")
```

### 2. Text Processing - Clean and Chunk Text

```python
from src.utils import TextCleaner, TextChunker, TokenCounter

# Clean text
cleaner = TextCleaner()
clean_text = cleaner.clean_text("  Messy   text   here  ")

# Count tokens
counter = TokenCounter(model="gpt-3.5-turbo")
tokens = counter.count_tokens(clean_text)

# Chunk text
chunker = TextChunker(chunk_size=1000, chunk_overlap=200)
chunks = chunker.chunk_by_characters(clean_text)
```

### 3. Cost Tracker - Track API Costs

```python
from src.utils import CostTracker

tracker = CostTracker(db_path="data/costs.db")

# Record usage
tracker.record_usage(
    model="gpt-4",
    provider="openai",
    operation="completion",
    prompt_tokens=100,
    completion_tokens=200,
    latency_ms=1500.0
)

# Get summary
summary = tracker.get_summary()
print(f"Total cost: ${summary['total_cost']:.4f}")
```

### 4. Validators - Validate Input

```python
from src.utils import validate_query, validate_file_type, ValidationError

try:
    validate_query("What is this document about?")
    validate_file_type("document.pdf")
except ValidationError as e:
    print(f"Error: {e.message}")
```

### 5. Helpers - Format Everything

```python
from src.utils import (
    format_datetime,
    format_file_size,
    format_cost,
    ResponseFormatter
)

from datetime import datetime

# Format datetime
print(format_datetime(datetime.now(), "human"))
# Output: "November 16, 2025 at 10:08 AM"

# Format file size
print(format_file_size(1536789))
# Output: "1.47 MB"

# Format cost
print(format_cost(0.00123))
# Output: "$0.001"

# Format API response
response = ResponseFormatter.success_response(
    data={"result": "success"},
    message="Operation completed"
)
```

## Common Use Cases

### RAG Pipeline Logging

```python
from src.utils import get_rag_logger, generate_uuid

rag_logger = get_rag_logger(__name__)
query_id = generate_uuid()

# Log query start
rag_logger.log_query_start(
    query_id=query_id,
    query="What is machine learning?",
    document_ids=["doc-1", "doc-2"],
    rag_strategy="hybrid"
)

# Log retrieval step
rag_logger.log_retrieval_step(
    query_id=query_id,
    step_name="semantic_search",
    num_results=10,
    latency_ms=150.5
)

# Log LLM generation
rag_logger.log_llm_generation(
    query_id=query_id,
    model="gpt-4",
    prompt_tokens=100,
    completion_tokens=200,
    total_tokens=300,
    cost=0.009,
    latency_ms=1500.0
)

# Log completion
rag_logger.log_query_complete(
    query_id=query_id,
    total_latency_ms=2000.0,
    total_tokens=300,
    total_cost=0.009,
    num_sources=5,
    success=True
)
```

### Document Processing

```python
from src.utils import (
    TextChunker,
    TokenCounter,
    validate_file_size,
    get_logger
)

logger = get_logger(__name__)

def process_document(file_path, file_size, text):
    # Validate
    validate_file_size(file_size)
    logger.info(f"Processing document: {file_path}")

    # Count tokens
    counter = TokenCounter()
    total_tokens = counter.count_tokens(text)
    logger.info(f"Document has {total_tokens} tokens")

    # Chunk
    chunker = TextChunker(chunk_size=1000, chunk_overlap=200)
    chunks = chunker.chunk_by_characters(text)
    logger.info(f"Created {len(chunks)} chunks")

    return chunks
```

### Cost Analytics Dashboard

```python
from src.utils import CostTracker, format_cost
from datetime import datetime, timedelta

tracker = CostTracker(db_path="data/costs.db")

# Get today's cost
today = datetime.now().replace(hour=0, minute=0, second=0)
today_cost = tracker.get_total_cost(start_date=today)
print(f"Today's cost: {format_cost(today_cost)}")

# Get usage by model
by_model = tracker.get_usage_by_model()
for model, stats in by_model.items():
    print(f"{model}: {format_cost(stats['total_cost'])} ({stats['total_tokens']} tokens)")

# Export report
tracker.export_to_csv("monthly_report.csv")
```

### Error Handling

```python
from src.utils import (
    ValidationError,
    format_error,
    ResponseFormatter
)

def api_endpoint(query):
    try:
        # Validate
        validate_query(query)

        # Process
        result = process_query(query)

        # Return success
        return ResponseFormatter.success_response(
            data=result,
            message="Query processed successfully"
        )

    except ValidationError as e:
        return ResponseFormatter.error_response(
            error=e,
            code="VALIDATION_ERROR",
            status_code=400
        )

    except Exception as e:
        error_details = format_error(e, include_traceback=True)
        return ResponseFormatter.error_response(
            error=str(e),
            code="INTERNAL_ERROR",
            status_code=500
        )
```

## All Available Imports

```python
from src.utils import (
    # Logger
    get_logger,
    get_rag_logger,
    setup_logging,
    RAGPipelineLogger,
    log_execution_time,
    log_async_execution_time,

    # Text Processing
    TextCleaner,
    TokenCounter,
    TextChunker,
    MetadataExtractor,
    TextChunk,

    # Cost Tracker
    CostTracker,
    UsageRecord,
    ModelPricing,

    # Validators
    ValidationError,
    FileValidator,
    QueryValidator,
    ConfigValidator,
    Sanitizer,
    validate_file_type,
    validate_file_size,
    validate_query,
    validate_config,
    sanitize_input,

    # Helpers
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
    generate_uuid,
)
```

## Next Steps

1. Initialize logging in your main app
2. Use validators for all user inputs
3. Track costs for all LLM API calls
4. Use text utilities for document processing
5. Format all API responses consistently

For detailed documentation, see: `UTILITIES_SUMMARY.md`
