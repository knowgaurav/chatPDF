# Docker Setup Guide for chatPDF

This guide will help you run the chatPDF application using Docker and Docker Compose.

## Prerequisites

- **Docker** (version 20.10 or higher)
- **Docker Compose** (version 2.0 or higher)
- At least **8GB RAM** available for Docker
- (Optional) **NVIDIA GPU** with Docker GPU support for faster local LLM inference

## Quick Start

### 1. Clone and Navigate to Repository

```bash
cd chatPDF
```

### 2. Configure Environment Variables

Copy the example environment file and edit it with your API keys:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```bash
# Required for OpenAI features
OPENAI_API_KEY=sk-your-openai-api-key-here

# Optional: For HuggingFace gated models
HF_API_KEY=hf_your_huggingface_token_here
```

**Note**: If you don't have an OpenAI API key, you can still use Ollama for local LLMs (see below).

### 3. Start the Application

Run everything with a single command:

```bash
docker-compose up
```

Or run in detached mode (background):

```bash
docker-compose up -d
```

### 4. Access the Application

- **chatPDF UI**: http://localhost:8501
- **Ollama API**: http://localhost:11434

### 5. Download Ollama Models (Optional)

To use local LLMs with Ollama, download models:

```bash
# Access Ollama container
docker exec -it chatpdf-ollama ollama pull llama3:8b

# Or pull other models
docker exec -it chatpdf-ollama ollama pull mistral:7b
docker exec -it chatpdf-ollama ollama pull codellama:7b
```

List available models:

```bash
docker exec -it chatpdf-ollama ollama list
```

## Architecture

The Docker setup includes two services:

### 1. chatpdf (Streamlit Application)
- **Port**: 8501
- **Volumes**:
  - `./data:/app/data` - Document uploads, vector stores, database
  - `./logs:/app/logs` - Application logs
- **Resource Limits**: 2 CPU cores, 4GB RAM

### 2. ollama (Local LLM Server)
- **Port**: 11434
- **Volume**: `ollama-models:/root/.ollama` - Model storage
- **Resource Limits**: 4 CPU cores, 8GB RAM

## Common Commands

### Start Services
```bash
docker-compose up -d
```

### Stop Services
```bash
docker-compose down
```

### View Logs
```bash
# All services
docker-compose logs -f

# Only chatPDF
docker-compose logs -f chatpdf

# Only Ollama
docker-compose logs -f ollama
```

### Restart Services
```bash
docker-compose restart
```

### Rebuild After Code Changes
```bash
docker-compose up --build
```

### Remove Everything (Including Volumes)
```bash
docker-compose down -v
```

## Data Persistence

All data is persisted in the following locations:

- **Documents**: `./data/uploads/`
- **Vector Stores**: `./data/vector_stores/`
- **Database**: `./data/chatpdf.db`
- **Logs**: `./logs/`
- **Ollama Models**: Docker volume `ollama-models`

To backup your data, simply copy the `./data` directory.

## Environment Variables

All environment variables are documented in `.env.example`. Key variables:

### Required
- `OPENAI_API_KEY` - For OpenAI GPT models (or use Ollama)

### Optional
- `OLLAMA_BASE_URL` - Ollama API URL (default: http://ollama:11434)
- `HF_API_KEY` - HuggingFace API token
- `CHUNK_SIZE` - Text chunk size (default: 1000)
- `TOP_K_RETRIEVAL` - Number of chunks to retrieve (default: 10)
- `USE_RERANKING` - Enable re-ranking (default: True)

## Troubleshooting

### Port Already in Use

If port 8501 or 11434 is already in use, edit `docker-compose.yml`:

```yaml
services:
  chatpdf:
    ports:
      - "8502:8501"  # Changed from 8501
```

### Out of Memory

Reduce resource limits in `docker-compose.yml`:

```yaml
deploy:
  resources:
    limits:
      memory: 2G  # Reduced from 4G
```

### Ollama Models Not Found

Make sure you've pulled models:

```bash
docker exec -it chatpdf-ollama ollama pull llama3:8b
```

### Permission Errors

Ensure data directories are writable:

```bash
chmod -R 755 data/ logs/
```

### Check Service Health

```bash
# chatPDF health
curl http://localhost:8501/_stcore/health

# Ollama health
curl http://localhost:11434/api/tags
```

## GPU Support (NVIDIA)

To enable GPU acceleration for Ollama:

1. Install [nvidia-docker](https://github.com/NVIDIA/nvidia-docker)

2. Uncomment GPU lines in `docker-compose.yml`:

```yaml
ollama:
  runtime: nvidia
  environment:
    - NVIDIA_VISIBLE_DEVICES=all
```

3. Restart services:

```bash
docker-compose down
docker-compose up -d
```

## Development Mode

For development with hot-reload:

1. Mount source code as volume in `docker-compose.yml`:

```yaml
chatpdf:
  volumes:
    - .:/app
    - ./data:/app/data
```

2. Restart on code changes:

```bash
docker-compose restart chatpdf
```

## Production Deployment

For production:

1. Update `.env`:
```bash
APP_ENV=production
DEBUG=False
```

2. Use proper secret keys:
```bash
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)
```

3. Enable HTTPS (use nginx reverse proxy)

4. Set resource limits appropriately

5. Enable monitoring and logging

## Updating

To update to the latest version:

```bash
git pull
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Support

For issues and questions:
- Check logs: `docker-compose logs -f`
- Review `.env` configuration
- Ensure Docker has sufficient resources
- Check HLD.md and LLD.md for architecture details

## Clean Start

To start fresh (WARNING: deletes all data):

```bash
docker-compose down -v
rm -rf data/ logs/
docker-compose up
```

---

**Happy chatting with your PDFs!**
