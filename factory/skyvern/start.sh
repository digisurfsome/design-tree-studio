#!/bin/bash
# ===========================================
# SKYVERN STARTUP SCRIPT
# ===========================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "  SKYVERN BROWSER AGENT - STARTUP"
echo "=========================================="

# Check for .env file
if [ ! -f .env ]; then
    echo "ERROR: .env file not found!"
    echo "Copy .env.example to .env and add your API keys:"
    echo "  cp .env.example .env"
    exit 1
fi

# Load environment variables
source .env

# Verify required keys
if [ -z "$ANTHROPIC_API_KEY" ] && [ -z "$OPENAI_API_KEY" ]; then
    echo "ERROR: At least one LLM API key required!"
    echo "Set ANTHROPIC_API_KEY or OPENAI_API_KEY in .env"
    exit 1
fi

echo "✓ Environment loaded"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker not installed!"
    echo "Install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "ERROR: Docker Compose not installed!"
    exit 1
fi

echo "✓ Docker ready"

# Create required directories
mkdir -p workflows recordings

# Start services
echo ""
echo "Starting Skyvern services..."
echo ""

docker-compose up -d

# Wait for services to be ready
echo ""
echo "Waiting for services to initialize..."
sleep 10

# Health check
echo ""
echo "Running health check..."

MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✓ Skyvern API is ready!"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "  Waiting for API... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "WARNING: API health check timed out"
    echo "Check logs with: docker-compose logs skyvern"
fi

echo ""
echo "=========================================="
echo "  SKYVERN IS RUNNING"
echo "=========================================="
echo ""
echo "  Web UI:     http://localhost:8080"
echo "  API:        http://localhost:8000"
echo "  API Docs:   http://localhost:8000/docs"
echo ""
echo "  Commands:"
echo "    Stop:     docker-compose down"
echo "    Logs:     docker-compose logs -f skyvern"
echo "    Restart:  docker-compose restart"
echo ""
echo "=========================================="
