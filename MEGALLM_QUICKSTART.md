# MegaLLM Quick Start Guide

Get started with chatPDF using MegaLLM in 5 minutes!

## Why MegaLLM?

**MegaLLM** provides access to multiple LLM providers (OpenAI, Anthropic, Google) through a single API key. No need to manage separate accounts and API keys!

### Benefits:
- ✅ **Single API Key** - One key for GPT, Claude, Gemini
- ✅ **Unified Billing** - One invoice for all LLM usage
- ✅ **Simple Setup** - Just add one environment variable
- ✅ **Cost-Effective** - Competitive pricing across providers

## Quick Setup

### Step 1: Get Your MegaLLM API Key

1. Visit https://megallm.io
2. Sign up for a free account
3. Go to Dashboard → API Keys
4. Generate a new API key
5. Copy your key (starts with `mega_`)

### Step 2: Configure chatPDF

```bash
# Copy the environment template
cp .env.example .env

# Edit .env and add your key
nano .env  # or use any text editor
```

Add this line to your `.env` file:
```bash
MEGALLM_API_KEY=mega_your_actual_key_here
```

### Step 3: Test Your Configuration

```bash
# Install dependencies if not already installed
pip install -r requirements.txt

# Run the test script
python test_megallm.py
```

You should see:
```
✅ All tests PASSED! MegaLLM integration is working correctly.
```

### Step 4: Start chatPDF

#### Option A: Docker (Recommended)
```bash
docker-compose up
```

#### Option B: Local Python
```bash
python init_db.py
streamlit run app.py
```

### Step 5: Use MegaLLM Models

In the chatPDF UI:
1. Upload a document (PDF, DOCX, TXT, or MD)
2. Select a MegaLLM model from the dropdown:
   - **MegaLLM GPT-5 Mini** - Fast and efficient
   - **MegaLLM Claude Haiku 4.5** - Balanced performance
   - **MegaLLM Gemini 2.5 Flash** - Ultra-fast responses
3. Ask questions about your document!

## Available Models

### MegaLLM GPT-5 Mini
- **Best for**: General questions, fast responses
- **Speed**: Very Fast
- **Cost**: Low
- **Model ID**: `gpt-5-mini`

### MegaLLM Claude Haiku 4.5
- **Best for**: Detailed analysis, longer responses
- **Speed**: Fast
- **Cost**: Medium
- **Model ID**: `claude-haiku-4-5`

### MegaLLM Gemini 2.5 Flash
- **Best for**: Quick queries, real-time chat
- **Speed**: Ultra Fast
- **Cost**: Very Low
- **Model ID**: `gemini-2-5-flash`

## Troubleshooting

### "API Key not found"
- Make sure `.env` file exists in the project root
- Check that `MEGALLM_API_KEY` is set correctly
- Restart the application

### "Invalid API Key"
- Verify your key at https://megallm.io/dashboard
- Make sure key starts with `mega_`
- Check for extra spaces or quotes

### "Model not found"
- Model IDs may have changed
- Verify exact model names at https://megallm.io/dashboard/models
- Update `src/providers/generic_api_provider.py` if needed

### Test Script Fails
```bash
# Check your internet connection
ping megallm.io

# Verify environment is loaded
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('MEGALLM_API_KEY'))"

# Check aiohttp is installed
pip install aiohttp
```

## Cost Tracking

chatPDF automatically tracks API usage and costs:

1. View **Usage Statistics** in the sidebar
2. See **per-query costs** in the chat interface
3. Check **total spending** in the analytics dashboard

## Example Usage

```python
from src.services.llm_service import LLMService

# Initialize service
llm_service = LLMService()

# Use MegaLLM model
response = await llm_service.generate(
    prompt="What is RAG?",
    model="MegaLLM GPT-5 Mini",
    temperature=0.7,
    max_tokens=500
)

print(response)
```

## Next Steps

- 📖 Read [MEGALLM_INTEGRATION.md](./MEGALLM_INTEGRATION.md) for advanced configuration
- 🔧 See [GENERIC_API_PROVIDER.md](./GENERIC_API_PROVIDER.md) for adding custom APIs
- 📚 Check [README.md](./README.md) for full documentation

## Support

- **MegaLLM Issues**: support@megallm.io
- **chatPDF Issues**: GitHub Issues
- **Documentation**: https://docs.megallm.io

---

**Ready to start chatting with your documents!** 🚀

Just run:
```bash
streamlit run app.py
```

And visit http://localhost:8501
