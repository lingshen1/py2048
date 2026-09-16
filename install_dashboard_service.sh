#!/bin/sh
# Installer Script for Calculinux Dashboard Service
# Execute as root on the target device!

echo "--- Installing Calculinux Dashboard Service ---"

# Copy the service file to systemd directory
CP_DIR="/etc/systemd/system"
if [ -d "$CP_DIR" ]; then
    cp calculinux-dashboard.service /etc/systemd/system/
    echo "1. Copied service file to /etc/systemd/system/"
    
    # Reload systemd daemon
    systemctl daemon-reload
    echo "2. Reloaded systemd daemon"
    
    # Enable the service to run on boot
    systemctl enable calculinux-dashboard.service
    echo "3. Enabled calculinux-dashboard.service on boot!"
    echo "------------------------------------------------"
    echo "Installation complete! The dashboard will start automatically on boot."
    echo "To start it now, run: systemctl start calculinux-dashboard.service"
else
    echo "Error: systemd directory /etc/systemd/system not found. Is this a systemd Linux system?"
fi
