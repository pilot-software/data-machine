#!/bin/bash

echo "🔧 Setting up HMS Terminology Service..."
echo ""

# Check Python 3.11 or 3.12
if command -v python3.12 &> /dev/null; then
    PYTHON="python3.12"
elif command -v python3.11 &> /dev/null; then
    PYTHON="python3.11"
elif command -v python3 &> /dev/null; then
    PYTHON="python3"
    echo "⚠️  Warning: Python 3.11 or 3.12 recommended (you have $(python3 --version))"
else
    echo "❌ Python 3 not found. Install Python 3.11 or 3.12:"
    echo "   brew install python@3.12"
    exit 1
fi

# Create venv
echo "📦 Creating virtual environment with $PYTHON..."
$PYTHON -m venv venv

# Activate venv
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q -r requirements.txt

echo ""
echo "✅ Setup complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Configure .env file (copy from .env.example)"
echo "   2. Download AB-HBP data: python scripts/etl/download_abhbp_data.py"
echo "   3. Start service: ./start.sh"
