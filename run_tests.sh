#!/bin/bash

# Test runner script for the gallery application

echo "🧪 Running Gallery Application Tests"
echo "=================================="

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Virtual environment not detected. Activating..."
    source .venv/bin/activate
fi

# Install test dependencies
echo "📦 Installing test dependencies..."
pip install -r requirements-test.txt

# Run tests with verbose output
echo "🚀 Running tests..."
python -m pytest tests/ -v --tb=short

# Check test results
if [ $? -eq 0 ]; then
    echo "✅ All tests passed!"
else
    echo "❌ Some tests failed. Check output above."
    exit 1
fi

echo "📊 Test coverage and results complete."
