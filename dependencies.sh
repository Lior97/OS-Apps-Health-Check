#!/bin/bash

# Exit script on any error
set -e

# Update package list and install Python3 and pip (for Debian-based systems)
# Add similar commands for other OS if needed
echo "Updating package list and installing Python3 and pip..."
if command -v apt > /dev/null; then
    sudo apt install -y python3 python3-pip
elif command -v yum > /dev/null; then
    sudo yum install -y python3 python3-pip
elif command -v pkg > /dev/null; then
    sudo pkg install -y python3 py37-pip
fi

# Install Python packages using pip
echo "Installing Python dependencies..."
sudo apt install -y python3-paramiko python3-requests python3-rich python3-winrm
