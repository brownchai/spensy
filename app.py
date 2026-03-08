from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv
from openai import OpenAI
import base64
import csv
import json
import os
from datetime import datetime
from io import BytesIO, StringIO
import uuid

load_dotenv()

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    file_ext = os.path.splitext(file.filename)[1]
    supported_exts = {'.pdf'} | set(IMAGE_MEDIA_TYPES.keys())
    if file_ext.lower() not in supported_exts:
        return jsonify({'error': 'Unsupported file type. Use PDF or image files.'}), 400

    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(UPLOAD_FOLDER, unique_filename)

    try:
        file.save(file_path)

        if file_ext.lower() == '.pdf':
            transactions = extract_transactions_from_pdf(file_path)
        else:
            transactions = extract_transactions_from_image(file_path, file_ext)

        os.remove(file_path)
        return jsonify({'success': True, 'transactions': transactions}), 200

    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({'error': str(e)}), 500


@app.route('/export-csv', methods=['POST'])
def export_csv():
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
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'}), 200


if __name__ == '__main__':
    app.run(debug=True, port=5000)
