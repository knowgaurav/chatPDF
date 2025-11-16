# MegaLLM Integration Guide

## Overview

**MegaLLM** (https://megallm.io) is a unified API gateway that provides access to multiple LLM providers through a single OpenAI-compatible API endpoint. This means you can access GPT, Claude, Gemini, and other models using one API key and consistent interface.

## Benefits of Using MegaLLM

✅ **Single API Key** - Access multiple providers with one key
✅ **OpenAI-Compatible** - Works with existing OpenAI code
✅ **Cost-Effective** - Competitive pricing across providers
✅ **Automatic Fallbacks** - Built-in model fallback support
✅ **Simplified Billing** - One invoice for all LLM usage

## Available Models via MegaLLM

Our chatPDF system includes pre-configured support for these MegaLLM models:

### OpenAI Models
- **MegaLLM GPT-5** - Latest GPT model ($2.25 per 1M tokens)
- **MegaLLM GPT-4o** - GPT-4 Optimized ($2.50 input, $10 output per 1M)

### Anthropic Claude Models
- **MegaLLM Claude 3.5 Sonnet** - Latest Claude ($18 per 1M tokens)
- **MegaLLM Claude Opus 4** - Most capable Claude ($15 input, $75 output per 1M)

### Google Gemini Models
- **MegaLLM Gemini 2.5 Pro** - Advanced Gemini ($1.25 input, $3.75 output per 1M)
- **MegaLLM Gemini 2.0 Flash** - Fast and cheap ($0.075 input, $0.25 output per 1M)

## Setup Instructions

### 1. Get Your MegaLLM API Key

1. Visit https://megallm.io
2. Sign up for an account
3. Navigate to API Keys section
4. Generate a new API key
5. Copy your API key (starts with `mega_...`)

### 2. Configure in chatPDF

#### Option A: Environment Variable (Recommended)

Add to your `.env` file:
```bash
MEGALLM_API_KEY=mega_your_api_key_here
```

#### Option B: Configure in UI

1. Open chatPDF Streamlit app
2. Go to Settings sidebar
3. Select "Configure Custom API"
4. Enter:
   - **Provider Name**: MegaLLM
   - **API Key**: Your MegaLLM key
   - **Base URL**: `https://ai.megallm.io/v1`
   - **Model**: Choose from available models
   - **API Format**: Select "OpenAI Compatible"

### 3. Select a MegaLLM Model

In the chatPDF UI:
1. Navigate to LLM settings
2. Choose any "MegaLLM" prefixed model from the dropdown
3. Start chatting!

## Usage Examples

### Using MegaLLM in Code

```python
from src.providers.generic_api_provider import GenericAPIProvider, APIConfig

# Configure MegaLLM
megallm_config = APIConfig(
    name="MegaLLM GPT-5",
    api_key="mega_your_api_key",
    base_url="https://ai.megallm.io/v1",
    model="gpt-5",
    api_format="openai",
    cost_per_1k_input=0.00225,
    cost_per_1k_output=0.00225
)

# Create provider
provider = GenericAPIProvider([megallm_config])

# Generate response
response = await provider.generate(
    prompt="What is RAG?",
    model="gpt-5",
    temperature=0.7,
    max_tokens=500
)

print(response)
```

### Streaming Responses

```python
# Stream tokens as they're generated
async for chunk in provider.generate_stream(
    prompt="Explain vector databases",
    model="claude-3.5-sonnet",
    temperature=0.7
):
    print(chunk, end="", flush=True)
```

## Cost Comparison

| Model | Provider | Input (per 1M) | Output (per 1M) |
|-------|----------|----------------|-----------------|
| GPT-5 | MegaLLM | $2.25 | $2.25 |
| GPT-4o | MegaLLM | $2.50 | $10.00 |
| Claude 3.5 Sonnet | MegaLLM | $18.00 | $18.00 |
| Claude Opus 4 | MegaLLM | $15.00 | $75.00 |
| Gemini 2.5 Pro | MegaLLM | $1.25 | $3.75 |
| Gemini 2.0 Flash | MegaLLM | $0.075 | $0.25 |

## Features Supported

### ✅ Supported
- Chat completions
- Streaming responses
- Message history
- Temperature control
- Max tokens configuration
- Top-p sampling
- Cost tracking
- Multiple models

### ⚠️ MegaLLM-Specific Features
- **Fallback models**: Automatic fallback if primary model fails
- **Rate limit handling**: Built-in rate limit management
- **Unified billing**: Single invoice across all models

## Advanced Configuration

### Custom Model Configuration

Add any MegaLLM model not in the presets:

```python
from src.providers.generic_api_provider import get_predefined_apis

# Get predefined configs
configs = get_predefined_apis()

# Add custom MegaLLM model
custom_config = APIConfig(
    name="MegaLLM Custom Model",
    api_key=os.getenv("MEGALLM_API_KEY"),
    base_url="https://ai.megallm.io/v1",
    model="your-model-name",  # Any model from MegaLLM catalog
    api_format="openai",
    cost_per_1k_input=0.001,
    cost_per_1k_output=0.002
)
```

### Using Fallback Models

MegaLLM supports automatic fallback to alternative models if the primary fails:

```python
# Configure in request payload
payload = {
    "model": "gpt-5",
    "fallback_models": ["gpt-4o", "claude-3.5-sonnet"],
    "messages": [{"role": "user", "content": "Hello"}]
}
```

## Troubleshooting

### Issue: "Invalid API Key"
**Solution**:
- Verify your API key is correct
- Check it starts with `mega_`
- Ensure you've added billing info to your MegaLLM account

### Issue: "Model not found"
**Solution**:
- Check model name exactly matches MegaLLM catalog
- Model IDs are case-sensitive
- Visit https://docs.megallm.io/home/models for current list

### Issue: "Rate limit exceeded"
**Solution**:
- MegaLLM has built-in rate limiting
- Upgrade your MegaLLM plan for higher limits
- Use fallback models to distribute load

### Issue: Slow responses
**Solution**:
- Use faster models like `gemini-2.0-flash-001`
- Enable streaming for better perceived performance
- Check MegaLLM status page for any incidents

## Best Practices

1. **Start with cheaper models** - Use Gemini Flash for testing
2. **Enable streaming** - Better user experience
3. **Monitor costs** - Use built-in cost tracking
4. **Use fallbacks** - Configure fallback models for reliability
5. **Cache results** - Cache common queries to save costs

## API Documentation

For complete MegaLLM API documentation:
- **Docs**: https://docs.megallm.io
- **Models**: https://docs.megallm.io/home/models
- **Pricing**: https://megallm.io/pricing
- **Status**: https://status.megallm.io

## Support

- **MegaLLM Support**: support@megallm.io
- **chatPDF Issues**: GitHub Issues
- **Community**: Discord/Slack channels

## Comparison with Other Providers

### MegaLLM vs Direct APIs

**Advantages of MegaLLM:**
- ✅ Single API key for all models
- ✅ Unified billing
- ✅ Built-in fallbacks
- ✅ Simplified integration
- ✅ No need to manage multiple accounts

**Advantages of Direct APIs:**
- ✅ Slightly lower latency
- ✅ Direct access to all provider features
- ✅ No intermediary dependency

### When to Use MegaLLM

Use MegaLLM when:
- You want to experiment with multiple models
- You prefer unified billing
- You need automatic fallbacks
- You want simplified management

Use direct APIs when:
- You only use one provider
- You need absolute lowest latency
- You need provider-specific features

## Example: Full RAG Pipeline with MegaLLM

```python
import asyncio
from src.services.rag_service import RAGService
from src.providers.generic_api_provider import GenericAPIProvider, APIConfig

async def main():
    # Configure MegaLLM
    provider = GenericAPIProvider([
        APIConfig(
            name="MegaLLM Gemini Flash",
            api_key=os.getenv("MEGALLM_API_KEY"),
            base_url="https://ai.megallm.io/v1",
            model="gemini-2.0-flash-001",
            api_format="openai"
        )
    ])

    # Create RAG service
    rag_service = RAGService(
        vector_service=vector_service,
        search_service=search_service,
        llm_service=provider
    )

    # Query documents
    result = await rag_service.query(
        question="What are the key findings?",
        document_ids=["doc123"],
        config={
            "model": "gemini-2.0-flash-001",
            "temperature": 0.7,
            "use_reranking": True
        }
    )

    print(f"Answer: {result.answer}")
    print(f"Sources: {result.sources}")
    print(f"Cost: ${result.metadata.cost:.4f}")

asyncio.run(main())
```

---

**Happy chatting with MegaLLM!** 🚀
