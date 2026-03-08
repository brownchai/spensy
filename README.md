# Statement Parser - Transaction Extractor

A web application that extracts transaction details from bank statement images or PDFs and exports them to CSV format.

## Features

- 📄 Upload statement images (JPG, PNG, BMP, GIF) or PDFs
- 🔍 Automatic OCR text extraction and transaction detection
- 📊 Display extracted transactions in a table
- 💾 Export transactions to CSV format
- 🎨 Clean, responsive UI with drag-and-drop support

## Tech Stack

- **Backend**: Flask (Python web framework)
- **Frontend**: HTML5, CSS3, JavaScript
- **OCR**: pytesseract (Tesseract)
- **PDF Processing**: PyPDF2 and pdf2image
- **Data Export**: CSV format

## Prerequisites

Before you begin, ensure you have the following installed:

1. **Python 3.8+** - [Download](https://www.python.org/downloads/)
2. **Tesseract OCR** - Required for image text extraction
   - **macOS**: `brew install tesseract`
   - **Windows**: Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
   - **Linux**: `sudo apt-get install tesseract-ocr`

## Installation & Setup

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Verify Tesseract Installation

After installing Tesseract, verify it's accessible:

```bash
# On macOS/Linux
which tesseract

# On Windows, check installation path
```

If Tesseract is installed in a non-default location, you'll need to specify the path in `app.py`:

```python
import pytesseract
pytesseract.pytesseract.pytesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Windows
pytesseract.pytesseract.pytesseract_cmd = '/usr/local/bin/tesseract'  # macOS
```

### 3. Run the Application

**Terminal 1 - Start the Flask backend:**

```bash
python app.py
```

The backend will start on `http://localhost:5000`

**Terminal 2 - Start a simple HTTP server for the frontend:**

```bash
# macOS/Linux
python -m http.server 8000

# Or use any other method to serve index.html
```

The frontend will be available on `http://localhost:8000`

## Usage

1. Open `http://localhost:8000` in your browser
2. Click to browse or drag-and-drop a statement image/PDF
3. Wait for the transaction extraction to complete
4. Review the extracted transactions in the table
5. Click "Export to CSV" to download the transactions as a CSV file

## Transaction Parsing

The app automatically detects transactions with the following patterns:

- **Date**: Supports formats like `2024-03-15`, `15/03/2024`, `03/15/2024`
- **Amount**: Detects currency symbols and numeric values (e.g., `$1,234.56`, `€500.00`)
- **Description**: Extracts remaining text as transaction description

## Project Structure

```
spensy/
├── app.py              # Flask backend application
├── index.html          # Frontend UI
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Troubleshooting

### Issue: "pytesseract" not found
**Solution**: Make sure Tesseract is installed. Install it using:
- macOS: `brew install tesseract`
- Windows: Download from [here](https://github.com/UB-Mannheim/tesseract/wiki)
- Linux: `sudo apt-get install tesseract-ocr`

### Issue: CORS errors when uploading
**Solution**: The app has CORS enabled, but make sure you're accessing from `http://localhost:8000` or adjust the Flask origin in `app.py`

### Issue: PDF extraction is slow
**Solution**: This is normal for large PDFs with many pages. PyPDF2 will extract text directly, but if that fails, it falls back to OCR which is slower.

### Issue: Poor transaction detection
**Solution**: Transaction detection relies on regex patterns. For better accuracy with custom statement formats, modify the `parse_transactions()` function in `app.py` to match your specific statement format.

## Future Enhancements

- [ ] Support for more statement formats (invoice, receipt)
- [ ] ML-based transaction categorization
- [ ] Database storage option
- [ ] Multi-file batch processing
- [ ] Transaction duplicate detection
- [ ] Custom regex pattern configuration

## License

This project is open source and available under the MIT License.

## Support

For issues or feature requests, please create an issue in the repository.
