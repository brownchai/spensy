#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🚀 Statement Parser Setup"
echo "========================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed. Please install Python 3.8 or higher.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python found:${NC} $(python3 --version)"
echo ""

# Check if Tesseract is installed
if ! command -v tesseract &> /dev/null; then
    echo -e "${RED}❌ Tesseract OCR is not installed.${NC}"
    echo -e "${YELLOW}Install it using:${NC}"
    echo "  macOS: brew install tesseract"
    echo "  Ubuntu/Debian: sudo apt-get install tesseract-ocr"
    echo "  Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki"
    exit 1
fi

echo -e "${GREEN}✓ Tesseract found:${NC} $(tesseract --version | head -n 1)"
echo ""

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt

echo ""
echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo -e "${YELLOW}To run the application:${NC}"
echo ""
echo "1. In one terminal, start the Flask backend:"
echo "   source venv/bin/activate"
echo "   python app.py"
echo ""
echo "2. In another terminal, start the frontend server:"
echo "   python -m http.server 8000"
echo ""
echo "3. Open http://localhost:8000 in your browser"
echo ""
