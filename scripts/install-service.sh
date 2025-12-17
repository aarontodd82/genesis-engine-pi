#!/bin/bash
# Install GenesisEngine emulator bridge as a systemd service
# Run with: sudo ./install-service.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_FILE="$SCRIPT_DIR/genesis-bridge.service"
INSTALL_DIR="/home/pi/GenesisEngine-Pi"

echo "Installing GenesisEngine Emulator Bridge service..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run with sudo: sudo $0"
    exit 1
fi

# Install zeroconf for mDNS support
echo "Installing dependencies..."
pip3 install zeroconf 2>/dev/null || pip install zeroconf

# Update paths in service file if needed
ACTUAL_DIR="$(dirname "$SCRIPT_DIR")"
if [ "$ACTUAL_DIR" != "$INSTALL_DIR" ]; then
    echo "Updating service paths for: $ACTUAL_DIR"
    sed -i "s|$INSTALL_DIR|$ACTUAL_DIR|g" "$SERVICE_FILE"
fi

# Copy service file
echo "Installing systemd service..."
cp "$SERVICE_FILE" /etc/systemd/system/genesis-bridge.service

# Reload systemd and enable service
systemctl daemon-reload
systemctl enable genesis-bridge.service

echo ""
echo "Installation complete!"
echo ""
echo "Commands:"
echo "  sudo systemctl start genesis-bridge    # Start the service"
echo "  sudo systemctl stop genesis-bridge     # Stop the service"
echo "  sudo systemctl status genesis-bridge   # Check status"
echo "  journalctl -u genesis-bridge -f        # View logs"
echo ""
echo "The service will auto-start on boot."
echo "To start now, run: sudo systemctl start genesis-bridge"
