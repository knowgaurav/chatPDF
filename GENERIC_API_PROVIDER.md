# Generic API Provider - Multi-LLM Support

## Overview

The chatPDF system now includes a **Generic API Provider** that allows you to use any LLM API endpoint with a simple configuration. No need for provider-specific code - just configure your API key and base URL!

## Supported API Formats

### 1. OpenAI-Compatible APIs
Works with any API that follows the OpenAI format:
- ✅ **OpenAI** (GPT-4, GPT-3.5-turbo)
- ✅ **MegaLLM** (Unified access to GPT, Claude, Gemini)
- ✅ **OpenRouter** (Access 100+ models)
- ✅ **Together AI** (Open source models)
- ✅ **Groq** (Ultra-fast inference)
- ✅ **Anyscale** (Scalable LLM endpoints)
- ✅ **Perplexity** (Search-augmented LLMs)
- ✅ **Any self-hosted OpenAI-compatible API**

### 2. Google Gemini API
Direct integration with Google's Gemini models:
- ✅ Gemini Pro
- ✅ Gemini Flash
- ✅ Gemini 2.0 series

### 3. Anthropic Claude API
Direct integration with Claude models:
- ✅ Claude 3.5 Sonnet
- ✅ Claude Opus
- ✅ Claude Haiku

## How It Works

### Configuration Structure

Each API requires just 4 essential fields:

```python
{
    "name": "Display Name",           # What shows in UI
    "api_key": "your-api-key",        # Your API key
    "base_url": "https://api...",     # API endpoint
    "model": "model-name",             # Model identifier
    "api_format": "openai"             # openai/gemini/claude
}
```

### Example Configurations

#### MegaLLM (Recommended)
```python
{
    "name": "MegaLLM GPT-5",
    "api_key": "mega_...",
    "base_url": "https://ai.megallm.io/v1",
    "model": "gpt-5",
    "api_format": "openai"
}
```

#### OpenRouter
```python
{
    "name": "OpenRouter GPT-4",
    "api_key": "sk-or-...",
    "base_url": "https://openrouter.ai/api/v1",
    "model": "openai/gpt-4",
    "api_format": "openai"
}
```

#### Groq
```python
{
    "name": "Groq Mixtral",
    "api_key": "gsk_...",
    "base_url": "https://api.groq.com/openai/v1",
    "model": "mixtral-8x7b-32768",
    "api_format": "openai"
}
```

#### Together AI
```python
{
    "name": "Together Mixtral",
    "api_key": "...",
    "base_url": "https://api.together.xyz/v1",
    "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
    "api_format": "openai"
}
```

#### Google Gemini (Direct)
```python
{
    "name": "Gemini Pro",
    "api_key": "AIza...",
    "base_url": "https://generativelanguage.googleapis.com",
    "model": "gemini-pro",
    "api_format": "gemini"
}
```

#### Anthropic Claude (Direct)
```python
{
    "name": "Claude 3.5",
    "api_key": "sk-ant-...",
    "base_url": "https://api.anthropic.com",
    "model": "claude-3-5-sonnet-20240620",
    "api_format": "claude"
}
```

## Pre-Configured Providers

The system comes with pre-configured templates for popular providers. Just add your API key!

Available templates:
1. **OpenAI GPT-4**
2. **OpenAI GPT-3.5**
3. **Google Gemini Pro**
4. **Anthropic Claude 3**
5. **OpenRouter**
6. **Together AI**
7. **Groq**
8. **MegaLLM GPT-5** ⭐
9. **MegaLLM GPT-4o** ⭐
10. **MegaLLM Claude 3.5 Sonnet** ⭐
11. **MegaLLM Claude Opus 4** ⭐
12. **MegaLLM Gemini 2.5 Pro** ⭐
13. **MegaLLM Gemini 2.0 Flash** ⭐

## Usage in Code

### Basic Usage

```python
from src.providers.generic_api_provider import GenericAPIProvider, APIConfig

# Create configuration
config = APIConfig(
    name="MegaLLM GPT-5",
    api_key="mega_your_key_here",
    base_url="https://ai.megallm.io/v1",
    model="gpt-5",
    api_format="openai",
    cost_per_1k_input=0.00225,
    cost_per_1k_output=0.00225
)

# Initialize provider
provider = GenericAPIProvider([config])

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
# Stream tokens as they arrive
async for chunk in provider.generate_stream(
    prompt="Explain vector databases in detail",
    model="gpt-5",
    temperature=0.7,
    max_tokens=1000
):
    print(chunk, end="", flush=True)
```

### Multiple Providers

```python
# Configure multiple providers at once
configs = [
    APIConfig(name="MegaLLM GPT", api_key="mega_...", ...),
    APIConfig(name="Groq Mixtral", api_key="gsk_...", ...),
    APIConfig(name="Together Llama", api_key="together_...", ...)
]

provider = GenericAPIProvider(configs)

# List all configured models
models = provider.list_models()
print(models)  # ['MegaLLM GPT', 'Groq Mixtral', 'Together Llama']

# Use any model
response = await provider.generate(prompt="Hello", model="Groq Mixtral")
```

### Chat Completions

```python
from src.providers.base_provider import Message

# Multi-turn conversation
messages = [
    Message(role="system", content="You are a helpful assistant"),
    Message(role="user", content="What is a vector database?"),
    Message(role="assistant", content="A vector database stores..."),
    Message(role="user", content="How does FAISS work?")
]

result = await provider.chat(
    messages=messages,
    model="gpt-5",
    temperature=0.7,
    max_tokens=500
)

print(result.content)
print(f"Cost: ${result.cost:.4f}")
```

## Adding Custom APIs

### Add a New OpenAI-Compatible API

```python
# Any OpenAI-compatible API
custom_config = APIConfig(
    name="My Custom API",
    api_key="your_key",
    base_url="https://your-api.com/v1",
    model="your-model-name",
    api_format="openai"  # Use OpenAI adapter
)

provider.add_api(custom_config)
```

### Self-Hosted LLMs

```python
# Self-hosted OpenAI-compatible server
local_config = APIConfig(
    name="Local LLM",
    api_key="not-needed",  # Some self-hosted don't need keys
    base_url="http://localhost:8000/v1",
    model="llama-3-70b",
    api_format="openai",
    cost_per_1k_input=0.0,  # Free for self-hosted
    cost_per_1k_output=0.0
)
```

## Configuration in UI

### Environment Variables (.env)

```bash
# MegaLLM
MEGALLM_API_KEY=mega_your_key_here

# OpenRouter
OPENROUTER_API_KEY=sk-or-your_key_here

# Groq
GROQ_API_KEY=gsk_your_key_here

# Together AI
TOGETHER_API_KEY=your_key_here

# Traditional providers
OPENAI_API_KEY=sk-your_key_here
ANTHROPIC_API_KEY=sk-ant-your_key_here
GOOGLE_API_KEY=AIza_your_key_here
```

### Streamlit UI (Coming Soon)

In the chatPDF UI, you'll be able to:
1. Select from pre-configured providers
2. Add custom API endpoints
3. Switch between providers on-the-fly
4. Monitor costs per provider
5. Compare responses across providers

## Cost Tracking

All providers support automatic cost tracking:

```python
# Costs are calculated automatically
result = await provider.chat(messages, model="gpt-5")

print(f"Input tokens: {result.input_tokens}")
print(f"Output tokens: {result.output_tokens}")
print(f"Total cost: ${result.cost:.4f}")
```

Cost tracking uses the configured pricing:
- `cost_per_1k_input`: Cost per 1,000 input tokens
- `cost_per_1k_output`: Cost per 1,000 output tokens

## Adapter System

The generic provider uses adapters to translate between formats:

### OpenAI Adapter
```python
# Handles request/response format for:
# - OpenAI, MegaLLM, OpenRouter, Groq, Together, etc.
{
    "model": "gpt-5",
    "messages": [...],
    "temperature": 0.7,
    "max_tokens": 500
}
```

### Gemini Adapter
```python
# Converts to Gemini's format:
{
    "contents": [{"role": "user", "parts": [{"text": "..."}]}],
    "generationConfig": {...}
}
```

### Claude Adapter
```python
# Converts to Claude's format:
{
    "model": "claude-3-5-sonnet",
    "messages": [...],
    "system": "...",
    "max_tokens": 500
}
```

## Benefits

### 1. **Flexibility**
- Use any API provider
- Switch providers without code changes
- Test multiple providers easily

### 2. **Cost Optimization**
- Compare prices across providers
- Use cheaper alternatives (Groq, Together AI)
- Track costs per provider

### 3. **Reliability**
- Fallback to alternative providers
- No vendor lock-in
- Easy provider migration

### 4. **Simplicity**
- One interface for all providers
- Minimal configuration needed
- Consistent API across all models

## Comparison: Provider Options

| Provider | Format | Speed | Cost | Models |
|----------|--------|-------|------|--------|
| **MegaLLM** | OpenAI | Fast | Medium | GPT, Claude, Gemini |
| OpenAI Direct | OpenAI | Fast | High | GPT series only |
| Groq | OpenAI | Very Fast | Very Low | Mixtral, Llama |
| Together AI | OpenAI | Fast | Low | Many open source |
| OpenRouter | OpenAI | Medium | Variable | 100+ models |
| Google Direct | Gemini | Fast | Low-Medium | Gemini only |
| Claude Direct | Claude | Fast | High | Claude only |

## Recommended Setup

For most users, we recommend:

**Option 1: MegaLLM Only (Simplest)**
- Single API key
- Access to GPT, Claude, Gemini
- Unified billing
- Built-in fallbacks

**Option 2: Mixed Providers (Best Value)**
- MegaLLM for GPT, Claude, Gemini
- Groq for fast, cheap inference
- Self-hosted for privacy-sensitive tasks

**Option 3: Direct APIs (Maximum Control)**
- OpenAI for latest GPT models
- Anthropic for Claude
- Google for Gemini
- More management, but full control

## Next Steps

1. **Get API Keys**: Sign up for your chosen provider(s)
2. **Configure**: Add keys to `.env` or configure in UI
3. **Test**: Try different models and compare
4. **Optimize**: Monitor costs and adjust

## Documentation Links

- **MegaLLM**: [MEGALLM_INTEGRATION.md](./MEGALLM_INTEGRATION.md)
- **Main README**: [README.md](./README.md)
- **Project Summary**: [PROJECT_SUMMARY.md](./PROJECT_SUMMARY.md)

---

**Enjoy flexible multi-LLM support!** 🚀
