@echo off
REM Colors would require more complex setup, so using simple messages

echo.
echo 🚀 Statement Parser Setup
echo ========================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.8 or higher.
    echo Download from: https://www.python.org/downloads/
    exit /b 1
)

echo ✓ Python found:
python --version
echo.

REM Check if Tesseract is installed
tesseract --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Tesseract OCR is not installed.
    echo Install from: https://github.com/UB-Mannheim/tesseract/wiki
    exit /b 1
)

echo ✓ Tesseract found:
tesseract --version | findstr /R "tesseract"
echo.

REM Create virtual environment
echo 📦 Creating virtual environment...
python -m venv venv

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
echo 📥 Installing dependencies...
python -m pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt

echo.
echo ✅ Setup complete!
echo.
echo To run the application:
echo.
echo 1. In one terminal, start the Flask backend:
echo    venv\Scripts\activate.bat
echo    python app.py
echo.
echo 2. In another terminal, start the frontend server:
echo    python -m http.server 8000
echo.
echo 3. Open http://localhost:8000 in your browser
echo.
pause
