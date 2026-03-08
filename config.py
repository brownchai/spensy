# Configuration file for Statement Parser

# Flask Configuration
FLASK_ENV = 'development'
DEBUG = True
FLASK_PORT = 5000

# File Upload Configuration
MAX_FILE_SIZE_MB = 50
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'bmp', 'gif'}

# OCR Configuration
# For Tesseract path, set this if tesseract is not in your system PATH
# TESSERACT_CMD = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Windows
# TESSERACT_CMD = '/usr/local/bin/tesseract'  # macOS
# TESSERACT_CMD = '/usr/bin/tesseract'  # Linux

# Transaction Detection Patterns
# Customize these regex patterns to match your statement format
TRANSACTION_DATE_PATTERNS = [
    r'(\d{4}-\d{2}-\d{2})',      # YYYY-MM-DD
    r'(\d{2}/\d{2}/\d{4})',      # DD/MM/YYYY or MM/DD/YYYY
    r'(\d{1,2}/\d{1,2}/\d{2,4})', # Variable format
]

TRANSACTION_AMOUNT_PATTERN = r'[~$£€]?\s*(\d+[\d,.]*?(?:\.\d{2})?)'

# CSV Export Configuration
CSV_EXPORT_FOLDER = 'exports'
CSV_DELIMITER = ','

# CORS Configuration
CORS_ORIGINS = ['http://localhost:8000', 'http://localhost:3000', 'http://127.0.0.1:8000']
