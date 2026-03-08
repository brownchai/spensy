from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv
from openai import OpenAI
import base64
import csv
import json
import logging
import os
from datetime import datetime
from io import BytesIO, StringIO
import uuid

from config import MAX_FILE_SIZE_MB, FLASK_PORT

load_dotenv()

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

client = OpenAI()

EXTRACT_PROMPT = """Extract all financial transactions from this statement.
Return a JSON object with this exact structure:
{
  "transactions": [
    {"date": "YYYY-MM-DD", "description": "merchant or description", "amount": "123.45"}
  ]
}
Use ISO date format (YYYY-MM-DD). If only month/day is shown, infer the year from context.
Amount should be a numeric string without currency symbols.
If no transactions are found, return {"transactions": []}.
Return only the JSON object, no other text."""

IMAGE_MEDIA_TYPES = {
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.gif': 'image/gif',
    '.bmp': 'image/bmp',
    '.webp': 'image/webp',
}


def extract_transactions_from_image(file_path, file_ext):
    """Extract transactions from an image file using GPT-4o vision."""
    with open(file_path, 'rb') as f:
        image_data = base64.standard_b64encode(f.read()).decode('utf-8')

    media_type = IMAGE_MEDIA_TYPES[file_ext.lower()]
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{media_type};base64,{image_data}"}
                },
                {"type": "text", "text": EXTRACT_PROMPT}
            ]
        }],
        response_format={"type": "json_object"},
    )
    result = json.loads(response.choices[0].message.content)
    return result.get("transactions", [])


def extract_transactions_from_pdf(file_path):
    """Extract transactions from a PDF file using GPT-4o."""
    import PyPDF2
    text = ""
    with open(file_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text() or ""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role": "user",
            "content": f"{EXTRACT_PROMPT}\n\n---\n{text}"
        }],
        response_format={"type": "json_object"},
    )
    result = json.loads(response.choices[0].message.content)
    return result.get("transactions", [])


def cleanup(paths):
    """Delete a list of file paths, ignoring missing files."""
    for path in paths:
        if os.path.exists(path):
            os.remove(path)


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle multi-file upload and transaction extraction (up to 5 files)."""
    # Accept both 'files' and 'files[]' field names
    files = request.files.getlist('files') or request.files.getlist('files[]')
    files = [f for f in files if f.filename != '']

    if not files:
        return jsonify({'error': 'No files provided'}), 400

    if len(files) > 5:
        return jsonify({'error': 'Maximum 5 files allowed at once'}), 400

    supported_exts = {'.pdf'} | set(IMAGE_MEDIA_TYPES.keys())

    # Validate all files before saving any
    for file in files:
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in supported_exts:
            return jsonify({'error': f'Unsupported file type: {file.filename}. Use PDF or image files.'}), 400

        file.seek(0, 2)
        size = file.tell()
        file.seek(0)
        if size > MAX_FILE_SIZE_BYTES:
            return jsonify({'error': f'{file.filename} exceeds the {MAX_FILE_SIZE_MB}MB size limit.'}), 400

    saved_paths = []
    try:
        for file in files:
            file_ext = os.path.splitext(file.filename)[1]
            file_path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}{file_ext}")
            file.save(file_path)
            saved_paths.append((file_path, file_ext))

        all_transactions = []
        for file_path, file_ext in saved_paths:
            if file_ext.lower() == '.pdf':
                transactions = extract_transactions_from_pdf(file_path)
            else:
                transactions = extract_transactions_from_image(file_path, file_ext)
            all_transactions.extend(transactions)
            os.remove(file_path)

        return jsonify({'success': True, 'transactions': all_transactions}), 200

    except Exception as e:
        logger.exception("Error processing upload")
        cleanup([p for p, _ in saved_paths])
        return jsonify({'error': 'An error occurred while processing your files. Please try again.'}), 500


@app.route('/export-csv', methods=['POST'])
def export_csv():
    """Export transactions list to a CSV file."""
    try:
        data = request.json
        transactions = data.get('transactions', [])

        if not transactions:
            return jsonify({'error': 'No transactions to export'}), 400

        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=['date', 'description', 'amount'])
        writer.writeheader()
        writer.writerows(transactions)

        csv_bytes = BytesIO(output.getvalue().encode())
        csv_bytes.seek(0)

        return send_file(
            csv_bytes,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f"transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
    except Exception as e:
        logger.exception("Error exporting CSV")
        return jsonify({'error': 'An error occurred while exporting. Please try again.'}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'}), 200


if __name__ == '__main__':
    app.run(debug=True, port=FLASK_PORT)
