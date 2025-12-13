#!/bin/bash
# ===========================================
# SOFTWARE FACTORY - INITIAL SETUP
# ===========================================
# Run this once to set up the factory environment

set -e

echo "=========================================="
echo "  SOFTWARE FACTORY - SETUP"
echo "=========================================="
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check Python
echo "Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is required"
    echo "Install with: brew install python3 (Mac) or apt install python3 (Linux)"
    exit 1
fi
echo "✓ Python $(python3 --version | cut -d' ' -f2)"

# Check pip
echo "Checking pip..."
if ! command -v pip3 &> /dev/null; then
    echo "ERROR: pip3 is required"
    exit 1
fi
echo "✓ pip3 available"

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
pip3 install -r requirements.txt --quiet
echo "✓ Dependencies installed"

# Check Docker (optional)
echo ""
echo "Checking Docker (optional, for Skyvern)..."
if command -v docker &> /dev/null; then
    echo "✓ Docker available"
    DOCKER_AVAILABLE=true
else
    echo "⚠ Docker not found - Skyvern will not be available"
    echo "  Install from: https://docs.docker.com/get-docker/"
    DOCKER_AVAILABLE=false
fi

# Create directories
echo ""
echo "Creating directories..."
mkdir -p batches reports skyvern/workflows skyvern/recordings
echo "✓ Directories created"

# Setup Skyvern config
if [ ! -f skyvern/.env ]; then
    echo ""
    echo "Creating Skyvern config..."
    cp skyvern/.env.example skyvern/.env
    echo "✓ Created skyvern/.env (edit with your API keys)"
fi

# Create main .env if not exists
if [ ! -f .env ]; then
    echo ""
    echo "Creating main .env..."
    cat > .env << 'EOF'
# ===========================================
# SOFTWARE FACTORY CONFIGURATION
# ===========================================

# Hosting Provider (at least one required)
DIGITALOCEAN_API_KEY=
VULTR_API_KEY=

# DNS Provider
CLOUDFLARE_API_KEY=
CLOUDFLARE_ZONE_ID=

# LLM Keys (for Skyvern)
ANTHROPIC_API_KEY=
OPENAI_API_KEY=

# SSH Key Path
SSH_KEY_PATH=~/.ssh/id_rsa

# Template Repository
TEMPLATE_REPO=https://github.com/yourusername/lamp-saas-template.git

# Skyvern
SKYVERN_API_URL=http://localhost:8000
SKYVERN_API_KEY=sk-local-dev-key
EOF
    echo "✓ Created .env (edit with your API keys)"
fi

# Make scripts executable
echo ""
echo "Setting permissions..."
chmod +x scripts/*.py 2>/dev/null || true
chmod +x skyvern/start.sh 2>/dev/null || true
echo "✓ Permissions set"

# Summary
echo ""
echo "=========================================="
echo "  SETUP COMPLETE"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Edit .env with your API keys:"
echo "   nano .env"
echo ""
echo "2. Edit skyvern/.env with LLM keys:"
echo "   nano skyvern/.env"
echo ""

if [ "$DOCKER_AVAILABLE" = true ]; then
echo "3. Start Skyvern (optional):"
echo "   cd skyvern && ./start.sh"
echo ""
echo "4. Create your first batch:"
else
echo "3. Create your first batch:"
fi

echo "   cp batches/batch-template.yaml batches/batch-001.yaml"
echo "   nano batches/batch-001.yaml"
echo ""
echo "5. Run the factory:"
echo "   python3 scripts/factory_controller.py batches/batch-001.yaml --dry-run"
echo ""
echo "=========================================="
