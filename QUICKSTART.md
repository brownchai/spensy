# Quick Start Guide - Statement Parser

## 🚀 Getting Started in 5 Minutes

### Step 1: Install Prerequisites (One-time setup)

**On macOS:**
```bash
# Install Tesseract for OCR
brew install tesseract

# Install Python dependencies
pip install -r requirements.txt
```

**On Windows:**
1. Download and install Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run: `pip install -r requirements.txt`

**On Linux:**
```bash
sudo apt-get install tesseract-ocr
pip install -r requirements.txt
```

### Step 2: Start the Backend (Terminal 1)

```bash
python app.py
```

You should see: `Running on http://127.0.0.1:5000`

### Step 3: Start the Frontend (Terminal 2)

```bash
python -m http.server 8000
```

### Step 4: Open in Browser

Navigate to: **http://localhost:8000**

## 📝 Supported Statement Formats

The app can extract transactions from statements containing:

**Dates:**
- `2024-03-15` (YYYY-MM-DD)
- `15/03/2024` (DD/MM/YYYY)
- `03/15/2024` (MM/DD/YYYY)

**Amounts:**
- `$1,234.56`
- `€500`
- `£1000.00`
- `₹10,000`

**Example statement line:**
```
2024-03-15 Amazon Purchase $89.99
```

## 💡 Tips & Tricks

### 1. **Best Results with Clear Images**
- Use a well-lit photo of your statement
- Ensure the text is sharp and readable
- Portrait orientation works best

### 2. **PDF vs Image**
- **PDF**: Fastest extraction, direct text reading
- **Image**: Slower (uses OCR), but works with any screenshot

### 3. **Batch Processing**
- Download one CSV at a time
- Can process multiple statements sequentially

### 4. **Custom Parsing**
Edit the `parse_transactions()` function in `app.py` if your statement format is different:

```python
def parse_transactions(text):
    # Add custom regex patterns here
    # Match your specific statement format
    pass
```

## 🔧 Customization

### Change Transaction Detection Patterns

In `app.py`, modify these regex patterns:

```python
# For dates
date_patterns = [
    r'(\d{4}-\d{2}-\d{2})',  # Add more patterns here
]

# For amounts
amount_pattern = r'[~$£€]?\s*(\d+[\d,.]*?(?:\.\d{2})?)'
```

### Change Server Ports

- **Backend**: Edit `app.py` line: `app.run(debug=True, port=5000)`
- **Frontend**: Change `python -m http.server 8000` to different port

### Enable HTTPS (Production)

```python
from flask_sslify import SSLify
SSLify(app)
```

## ⚠️ Common Issues

### Issue: "ModuleNotFoundError: No module named 'pytesseract'"
```bash
pip install -r requirements.txt
```

### Issue: "tesseract is not installed or it's not in your PATH"
- macOS: `brew install tesseract`
- Windows: Install from [here](https://github.com/UB-Mannheim/tesseract/wiki)
- Linux: `sudo apt-get install tesseract-ocr`

### Issue: "No transactions found"
- Try a clearer image
- Ensure dates and amounts match expected formats
- Check if special characters are causing issues

### Issue: CORS Error
- Ensure you're accessing from `http://localhost:8000`
- Check that Flask server is running on `localhost:5000`

## 📊 CSV Output Format

Your exported CSV will have this structure:

```
date,description,amount
2024-03-15,Amazon Purchase,$89.99
2024-03-14,Gas Station,$45.00
2024-03-13,Coffee Shop,$5.50
```

## 🎯 Next Steps

1. **Test with a sample**: Take a screenshot of a mock statement and test it
2. **Customize parsing**: Adjust regex patterns to match your statement format
3. **Automate**: Can be integrated into larger workflows or scheduled jobs
4. **Extend**: Add database storage, categories, or budgeting features

## 📞 Support

If you encounter issues:
1. Check the browser console (F12) for JavaScript errors
2. Check the terminal running Flask for Python errors
3. Ensure both servers are running
4. Try with a simpler, clearer statement image

## 📚 Learn More

- Flask Documentation: https://flask.palletsprojects.com/
- Tesseract OCR: https://github.com/tesseract-ocr/tesseract
- Pytesseract: https://github.com/madmaze/pytesseract
