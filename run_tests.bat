@echo off
REM Test runner script for Windows

echo 🧪 Running Gallery Application Tests
echo ==================================

REM Check if virtual environment is activated
if not defined VIRTUAL_ENV (
    echo ⚠️  Virtual environment not detected. Activating...
    call .venv\Scripts\activate.bat
)

REM Install test dependencies
echo 📦 Installing test dependencies...
pip install -r requirements-test.txt

REM Run tests with verbose output
echo 🚀 Running tests...
python -m pytest tests/ -v --tb=short

REM Check test results
if %errorlevel% equ 0 (
    echo ✅ All tests passed!
) else (
    echo ❌ Some tests failed. Check output above.
    exit /b 1
)

echo 📊 Test coverage and results complete.
