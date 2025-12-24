#!/bin/bash

# QuickSpin AI Setup Script

set -e

echo "🚀 QuickSpin AI Setup"
echo "===================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.12"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python $required_version or higher is required. Found: $python_version"
    exit 1
fi
echo "✅ Python $python_version"

# Install uv if not present
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi
echo "✅ uv installed"

# Install dependencies
echo ""
echo "Installing dependencies..."
uv sync --all-extras
echo "✅ Dependencies installed"

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file..."
    cp .env.example .env
    echo "✅ .env file created"
    echo ""
    echo "⚠️  Please edit .env and add your configuration:"
    echo "   - GROQ_API_KEY"
    echo "   - MONGODB_URI"
    echo "   - JWT_SECRET_KEY"
    echo ""
else
    echo "✅ .env file already exists"
fi

# Create data directory for ChromaDB
mkdir -p data/chroma
echo "✅ Data directory created"

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env with your configuration"
echo "2. Start MongoDB (or use Docker Compose: make docker-up)"
echo "3. Run the development server: make run"
echo "4. Visit http://localhost:8000/api/v1/docs for API documentation"
echo ""
echo "For CLI usage: uv run python -m app.cli chat --token YOUR_JWT_TOKEN"
echo ""
