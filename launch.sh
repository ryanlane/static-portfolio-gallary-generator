#!/bin/bash

# Static Portfolio Gallery Generator - Launch Script
echo "🚀 Starting Static Portfolio Gallery Generator..."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Please run ./install.sh first."
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Check if dependencies are installed
echo "📦 Checking dependencies..."
if ! python3 -c "import fastapi, uvicorn, jinja2, PIL, exifread" 2>/dev/null; then
    echo "⚠️  Some dependencies are missing. Installing..."
    pip install -r requirements.txt
fi

# Kill any existing uvicorn processes
echo "🛑 Stopping any existing server..."
pkill -f uvicorn 2>/dev/null || true

# Start the server
echo "🌐 Starting server on http://localhost:8000"
echo "Press Ctrl+C to stop the server"
echo ""
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
