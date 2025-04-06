# OTA (Over-The-Air) Update System

This document describes how to prepare firmware for OTA updates and set up the OTA update server.

## Table of Contents
- [Firmware Preparation](#firmware-preparation)
- [OTA Server Setup](#ota-server-setup)
- [ESP32 Configuration](#esp32-configuration)
- [Security Considerations](#security-considerations)

## Firmware Preparation

### Prerequisites
- ESP-IDF development environment
- Python 3.x
- Required Python packages (install using `pip install -r requirements.txt`)
- OTA server running (see [OTA Server Setup](#ota-server-setup))

### Preparing the Firmware

1. Configure the OTA server URL in `prepare_ota.sh`:
```bash
# Edit the OTA_SERVER variable at the top of the script
OTA_SERVER="http://your-server.com:5000"  # Change this to your OTA server URL
```

2. Run the preparation script:
```bash
./prepare_ota.sh
```

The script will:
- Build the firmware
- Create an `ota` directory if it doesn't exist
- Copy the firmware binary to the OTA directory with version information
- Upload the firmware to the OTA server
- Download and save the latest version information from the server

The process includes:
1. Building the firmware
2. Calculating the checksum
3. Uploading to the OTA server
4. Verifying the upload
5. Fetching and saving the version information

### Script Output
The script will display:
- Build progress
- Upload status
- Final version information
- Server URL
- Local file locations

The `version.json` file will contain:
```json
{
    "version": "1.0.0",
    "url": "http://your-server.com/ota/xiaozhi-esp32-v1.0.0.bin",
    "checksum": "sha256_checksum_here"
}
```

## OTA Server Setup

### Python OTA Server

The OTA server is implemented in Python using Flask. It provides the following features:
- Firmware file serving
- Version information management
- Automatic checksum calculation
- Firmware upload capability
- CORS support

### Installation

1. Install required Python packages:
```bash
pip install -r requirements.txt
```

2. Start the server:
```bash
python ota_server.py
```

The server will run on `http://localhost:5000` by default.

### Server Endpoints

1. **Get Version Information**
   - Endpoint: `GET /ota/version.json`
   - Returns: Current version information in JSON format

2. **Download Firmware**
   - Endpoint: `GET /ota/<filename>`
   - Returns: Firmware binary file

3. **Upload New Firmware**
   - Endpoint: `POST /ota/upload`
   - Method: Multipart form data
   - Parameters:
     - `file`: Firmware binary file (.bin)
     - `version`: Version number (optional, defaults to 1.0.0)
   - Returns: Upload confirmation with version and checksum

### Example Upload Command

```bash
curl -X POST \
  -F "file=@ota/xiaozhi-esp32-v1.0.0.bin" \
  -F "version=1.0.0" \
  http://localhost:5000/ota/upload
```

## ESP32 Configuration

1. Set the OTA version URL in menuconfig:
```
CONFIG_OTA_VERSION_URL="http://your-server.com/ota/version.json"
```

2. Enable OTA updates in menuconfig:
```
Component config -> ESP HTTPS OTA -> Allow HTTP for OTA (for development)
```

## Security Considerations

### Development Environment
- Use HTTP for development and testing
- Enable CORS for local development
- No authentication required for uploads

### Production Environment
1. **HTTPS**
   - Use HTTPS for all communications
   - Obtain SSL certificate (e.g., from Let's Encrypt)
   - Configure the server to use SSL

2. **Authentication**
   - Add authentication to the upload endpoint
   - Use API keys or JWT tokens
   - Implement rate limiting

3. **Server Security**
   - Use a production WSGI server (e.g., Gunicorn)
   - Implement proper logging
   - Set up monitoring
   - Regular security updates

4. **Firmware Security**
   - Verify firmware signatures
   - Implement secure boot
   - Use encrypted communications

## Troubleshooting

### Common Issues

1. **Version Mismatch**
   - Ensure version numbers match between firmware and server
   - Check version.json format

2. **Connection Issues**
   - Verify server is running
   - Check network connectivity
   - Verify CORS settings

3. **Upload Failures**
   - Check file permissions
   - Verify file format (.bin)
   - Check server logs

### Logs
- Server logs are available in the console
- Enable debug mode for detailed logging
- Check ESP32 serial output for OTA update status

## Maintenance

### Regular Tasks
1. Update server dependencies
2. Monitor server logs
3. Backup firmware versions
4. Update SSL certificates
5. Review security settings

### Version Management
- Keep track of firmware versions
- Maintain backward compatibility
- Document changes between versions
- Test updates before deployment 