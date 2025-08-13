#!/bin/bash

# Static Portfolio Gallery Generator - Installation Script
echo "🖼️  Setting up Static Portfolio Gallery Generator..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ and try again."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p static/thumbs
mkdir -p templates/partials

echo "✅ Installation complete!"
echo ""
echo "To start the application:"
echo "  ./launch.sh"
echo ""
echo "Or manually:"
echo "1. Activate the virtual environment: source .venv/bin/activate"
echo "2. Run the server: python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo "3. Open http://localhost:8000 in your browser"
echo ""
echo "To reset the database, go to http://localhost:8000/settings"
