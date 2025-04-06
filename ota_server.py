from flask import Flask, send_file, jsonify, request
from flask_cors import CORS
import os
import hashlib
import json
from pathlib import Path

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
OTA_DIR = Path("ota")
VERSION_FILE = OTA_DIR / "version.json"

def calculate_checksum(file_path):
    """Calculate SHA256 checksum of a file"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

@app.route('/ota/')
def get_version():
    """Serve the version information"""
    if not VERSION_FILE.exists():
        return jsonify({"error": "Version file not found"}), 404
    
    with open(VERSION_FILE, 'r') as f:
        version_info = json.load(f)
    
    # Format the response to match ESP32's expected format
    response = {
        "firmware": {
            "version": version_info["version"],
            "url": version_info["url"]
        }
    }
    return jsonify(response)

@app.route('/ota/<filename>')
def serve_firmware(filename):
    """Serve the firmware file"""
    file_path = OTA_DIR / filename
    if not file_path.exists():
        return jsonify({"error": "Firmware file not found"}), 404
    
    # Update checksum in version.json if needed
    if filename.endswith('.bin'):
        checksum = calculate_checksum(file_path)
        with open(VERSION_FILE, 'r') as f:
            version_info = json.load(f)
        if version_info.get('checksum') != checksum:
            version_info['checksum'] = checksum
            with open(VERSION_FILE, 'w') as f:
                json.dump(version_info, f, indent=4)
    
    # Set proper headers for firmware download
    response = send_file(
        file_path,
        mimetype='application/octet-stream',
        as_attachment=True,
        download_name=filename
    )
    
    # Add headers for better download handling
    response.headers['Content-Length'] = file_path.stat().st_size
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    return response

@app.route('/ota/upload', methods=['POST'])
def upload_firmware():
    """Upload new firmware version"""
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    if not file.filename.endswith('.bin'):
        return jsonify({"error": "Only .bin files are allowed"}), 400
    
    # Save the file
    file_path = OTA_DIR / file.filename
    file.save(file_path)
    
    # Calculate checksum
    checksum = calculate_checksum(file_path)
    
    # Update version.json
    version = request.form.get('version', '1.0.0')
    version_info = {
        "version": version,
        "url": f"http://{request.host}/ota/{file.filename}",
        "checksum": checksum
    }
    
    with open(VERSION_FILE, 'w') as f:
        json.dump(version_info, f, indent=4)
    
    return jsonify({
        "message": "Firmware uploaded successfully",
        "version": version,
        "checksum": checksum
    })

if __name__ == '__main__':
    # Create OTA directory if it doesn't exist
    OTA_DIR.mkdir(exist_ok=True)
    
    # Run the server
    app.run(host='0.0.0.0', port=5000, debug=True) 