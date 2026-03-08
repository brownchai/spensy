from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from openai import OpenAI
import base64
import ipaddress
import json
import logging
import os
import socket
import threading
import time
import urllib.parse
import uuid
from concurrent.futures import ThreadPoolExecutor
import requests

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

# Thread pool for async callback processing (cap at 10 concurrent jobs)
_executor = ThreadPoolExecutor(max_workers=10)
_semaphore = threading.BoundedSemaphore(10)

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

_BLOCKED_NETWORKS = [
    ipaddress.ip_network('10.0.0.0/8'),
    ipaddress.ip_network('172.16.0.0/12'),
    ipaddress.ip_network('192.168.0.0/16'),
    ipaddress.ip_network('127.0.0.0/8'),
    ipaddress.ip_network('169.254.0.0/16'),
    ipaddress.ip_network('0.0.0.0/8'),
    ipaddress.ip_network('::1/128'),
    ipaddress.ip_network('fc00::/7'),
    ipaddress.ip_network('fe80::/10'),
]


def is_safe_callback_url(url):
    """Validate callback URL to prevent SSRF attacks.

    Rejects non-http/https schemes, URLs with credentials, and any hostname
    that resolves to a private, loopback, or link-local IP address.
    """
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ('http', 'https'):
            return False
        if parsed.username or parsed.password:
            return False
        hostname = parsed.hostname
        if not hostname:
            return False
        for addr_info in socket.getaddrinfo(hostname, None):
            ip = ipaddress.ip_address(addr_info[4][0])
            for network in _BLOCKED_NETWORKS:
                if ip in network:
                    return False
        return True
    except Exception:
        return False


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


def _deliver_callback(callback_url, payload, max_retries=3):
    """POST payload to callback_url with exponential backoff retries."""
    for attempt in range(max_retries):
        try:
            resp = requests.post(
                callback_url, json=payload, timeout=30, allow_redirects=False
            )
            resp.raise_for_status()
            return
        except Exception as exc:
            if attempt < max_retries - 1:
                logger.warning(
                    "Callback attempt %d/%d to %s failed: %s",
                    attempt + 1, max_retries, callback_url, exc,
                )
                time.sleep(2 ** attempt)
            else:
                logger.exception(
                    "All %d callback attempts to %s failed", max_retries, callback_url
                )


def process_and_callback(saved_paths, file_count, callback_url, request_id):
    """Process files in background and POST results to callback_url."""
    try:
        all_transactions = []
        for file_path, file_ext in saved_paths:
            if file_ext.lower() == '.pdf':
                transactions = extract_transactions_from_pdf(file_path)
            else:
                transactions = extract_transactions_from_image(file_path, file_ext)
            all_transactions.extend(transactions)
            os.remove(file_path)

        payload = {
            "request_id": request_id,
            "status": "completed",
            "files_processed": file_count,
            "transaction_count": len(all_transactions),
            "transactions": all_transactions,
        }
    except Exception:
        logger.exception("Error processing files for callback (request_id=%s)", request_id)
        cleanup([p for p, _ in saved_paths])
        payload = {
            "request_id": request_id,
            "status": "error",
            "message": "An error occurred while processing the uploaded files.",
        }
    finally:
        _semaphore.release()

    _deliver_callback(callback_url, payload)


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle multi-file upload and transaction extraction (up to 5 files).

    Form fields:
      files        - one or more statement files (PDF or image)
      callback_url - optional URL to POST results to asynchronously

    Synchronous response (no callback_url):
      200 { status, files_processed, transaction_count, transactions }

    Async response (callback_url provided):
      202 { status: "processing", request_id, message }
      Then POSTs { request_id, status, files_processed, transaction_count, transactions }
      to callback_url when processing completes.
    """
    files = request.files.getlist('files') or request.files.getlist('files[]')
    files = [f for f in files if f.filename != '']

    if not files:
        return jsonify({'error': 'No files provided'}), 400

    if len(files) > 5:
        return jsonify({'error': 'Maximum 5 files allowed at once'}), 400

    callback_url = request.form.get('callback_url', '').strip() or None

    if callback_url and not is_safe_callback_url(callback_url):
        return jsonify({'error': 'Invalid or disallowed callback URL'}), 400

    supported_exts = {'.pdf'} | set(IMAGE_MEDIA_TYPES.keys())

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

        if callback_url:
            if not _semaphore.acquire(blocking=False):
                cleanup([p for p, _ in saved_paths])
                return jsonify({'error': 'Server is busy. Please retry later.'}), 503

            request_id = str(uuid.uuid4())
            _executor.submit(
                process_and_callback,
                saved_paths, len(files), callback_url, request_id,
            )
            return jsonify({
                "status": "processing",
                "request_id": request_id,
                "message": "Files received. Results will be POSTed to your callback URL when processing completes.",
            }), 202

        all_transactions = []
        for file_path, file_ext in saved_paths:
            if file_ext.lower() == '.pdf':
                transactions = extract_transactions_from_pdf(file_path)
            else:
                transactions = extract_transactions_from_image(file_path, file_ext)
            all_transactions.extend(transactions)
            os.remove(file_path)

        return jsonify({
            "status": "completed",
            "files_processed": len(files),
            "transaction_count": len(all_transactions),
            "transactions": all_transactions,
        }), 200

    except Exception:
        logger.exception("Error processing upload")
        cleanup([p for p, _ in saved_paths])
        return jsonify({'error': 'An error occurred while processing your files. Please try again.'}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'}), 200


if __name__ == '__main__':
    app.run(debug=True, port=FLASK_PORT)
