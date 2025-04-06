#!/bin/bash

# Configuration
OTA_SERVER="http://192.168.200.221:5000"  # Change this to your OTA server URL

# Get the current version from the firmware
VERSION=$(grep 'CONFIG_APP_PROJECT_VER' sdkconfig | cut -d'"' -f2)
if [ -z "$VERSION" ]; then
    echo "Error: Could not find version in sdkconfig"
    exit 1
fi

# Create OTA directory if it doesn't exist
mkdir -p ota

# Build the firmware
echo "Building firmware..."
idf.py build

# Copy the firmware to OTA directory with version in filename
FIRMWARE_FILE="xiaozhi-esp32-v${VERSION}.bin"
cp build/xiaozhi-esp32.bin "ota/${FIRMWARE_FILE}"

# Calculate checksum
CHECKSUM=$(sha256sum "ota/${FIRMWARE_FILE}" | cut -d' ' -f1)

# Upload firmware to OTA server
echo "Uploading firmware to OTA server..."
UPLOAD_RESPONSE=$(curl -s -X POST \
    -F "file=@ota/${FIRMWARE_FILE}" \
    -F "version=${VERSION}" \
    "${OTA_SERVER}/ota/upload")

# Check if upload was successful
if echo "$UPLOAD_RESPONSE" | grep -q "successfully"; then
    echo "Firmware uploaded successfully"
else
    echo "Error uploading firmware:"
    echo "$UPLOAD_RESPONSE"
    exit 1
fi

# Get the updated version information
echo "Fetching version information..."
VERSION_INFO=$(curl -s "${OTA_SERVER}/ota/version.json")

# Save version information locally
echo "$VERSION_INFO" > ota/version.json

echo "OTA firmware preparation complete:"
echo "Version: ${VERSION}"
echo "Binary: ota/${FIRMWARE_FILE}"
echo "Version info: ota/version.json"
echo "Server URL: ${OTA_SERVER}" 