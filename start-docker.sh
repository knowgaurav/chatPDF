#!/bin/bash

# chatPDF Docker Startup Script
# This script helps you easily start the chatPDF application with Docker

set -e

echo "======================================"
echo "  chatPDF Docker Startup Script"
echo "======================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    echo "Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}Warning: .env file not found${NC}"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo -e "${YELLOW}Please edit .env and add your API keys${NC}"
    echo ""
    read -p "Do you want to edit .env now? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ${EDITOR:-nano} .env
    fi
fi

# Create necessary directories
echo "Creating data directories..."
mkdir -p data/uploads data/vector_stores data/models/huggingface logs

# Start Docker Compose
echo ""
echo "Starting chatPDF services..."
echo ""

# Use docker compose (newer) or docker-compose (older)
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

# Check if services are already running
if $DOCKER_COMPOSE ps | grep -q "Up"; then
    echo -e "${YELLOW}Services are already running${NC}"
    read -p "Do you want to restart them? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Restarting services..."
        $DOCKER_COMPOSE restart
    fi
else
    # Start services
    $DOCKER_COMPOSE up -d
fi

# Wait for services to be healthy
echo ""
echo "Waiting for services to start..."
sleep 5

# Check if chatPDF is running
if curl -s http://localhost:8501/_stcore/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ chatPDF is running!${NC}"
else
    echo -e "${YELLOW}⚠ chatPDF might still be starting...${NC}"
fi

# Check if Ollama is running
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Ollama is running!${NC}"
else
    echo -e "${YELLOW}⚠ Ollama might still be starting...${NC}"
fi

echo ""
echo "======================================"
echo -e "${GREEN}Services Started Successfully!${NC}"
echo "======================================"
echo ""
echo "Access chatPDF at: http://localhost:8501"
echo "Ollama API at: http://localhost:11434"
echo ""
echo "To download Ollama models, run:"
echo "  docker exec -it chatpdf-ollama ollama pull llama3:8b"
echo ""
echo "To view logs:"
echo "  $DOCKER_COMPOSE logs -f"
echo ""
echo "To stop services:"
echo "  $DOCKER_COMPOSE down"
echo ""
