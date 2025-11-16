.PHONY: help build up down restart logs clean pull-models test

# Default target
help:
	@echo "chatPDF Docker Management Commands"
	@echo "=================================="
	@echo ""
	@echo "  make build        - Build Docker images"
	@echo "  make up           - Start all services"
	@echo "  make down         - Stop all services"
	@echo "  make restart      - Restart all services"
	@echo "  make logs         - View logs (all services)"
	@echo "  make logs-app     - View chatPDF logs only"
	@echo "  make logs-ollama  - View Ollama logs only"
	@echo "  make pull-models  - Download Ollama models"
	@echo "  make shell-app    - Open shell in chatPDF container"
	@echo "  make shell-ollama - Open shell in Ollama container"
	@echo "  make clean        - Remove containers and volumes (WARNING: deletes data)"
	@echo "  make test         - Run tests"
	@echo "  make setup        - Initial setup (create .env, directories)"
	@echo ""

# Initial setup
setup:
	@echo "Setting up chatPDF..."
	@if [ ! -f .env ]; then \
		echo "Creating .env from .env.example..."; \
		cp .env.example .env; \
		echo "Please edit .env and add your API keys"; \
	fi
	@mkdir -p data/uploads data/vector_stores data/models/huggingface logs
	@echo "Setup complete!"

# Build Docker images
build:
	docker-compose build

# Start services
up: setup
	docker-compose up -d
	@echo ""
	@echo "Services started!"
	@echo "chatPDF: http://localhost:8501"
	@echo "Ollama API: http://localhost:11434"

# Start with build
up-build: setup
	docker-compose up -d --build

# Stop services
down:
	docker-compose down

# Restart services
restart:
	docker-compose restart

# View all logs
logs:
	docker-compose logs -f

# View chatPDF logs
logs-app:
	docker-compose logs -f chatpdf

# View Ollama logs
logs-ollama:
	docker-compose logs -f ollama

# Download Ollama models
pull-models:
	@echo "Downloading Llama 3 8B..."
	docker exec -it chatpdf-ollama ollama pull llama3:8b
	@echo "Downloading Mistral 7B..."
	docker exec -it chatpdf-ollama ollama pull mistral:7b
	@echo "Models downloaded!"
	@echo ""
	@echo "Available models:"
	docker exec -it chatpdf-ollama ollama list

# List Ollama models
list-models:
	docker exec -it chatpdf-ollama ollama list

# Shell into chatPDF container
shell-app:
	docker exec -it chatpdf-app /bin/bash

# Shell into Ollama container
shell-ollama:
	docker exec -it chatpdf-ollama /bin/bash

# Run tests
test:
	docker exec -it chatpdf-app pytest tests/

# Clean everything (WARNING: deletes data)
clean:
	@echo "WARNING: This will delete all data!"
	@read -p "Are you sure? (y/N) " -n 1 -r; \
	echo ""; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v; \
		rm -rf data/ logs/; \
		echo "Cleaned!"; \
	fi

# Check service health
health:
	@echo "Checking chatPDF health..."
	@curl -s http://localhost:8501/_stcore/health && echo "✓ chatPDF is healthy" || echo "✗ chatPDF is not responding"
	@echo ""
	@echo "Checking Ollama health..."
	@curl -s http://localhost:11434/api/tags > /dev/null && echo "✓ Ollama is healthy" || echo "✗ Ollama is not responding"

# Show resource usage
stats:
	docker stats chatpdf-app chatpdf-ollama

# Backup data
backup:
	@mkdir -p backups
	@tar -czf backups/chatpdf-backup-$$(date +%Y%m%d-%H%M%S).tar.gz data/
	@echo "Backup created in backups/"
