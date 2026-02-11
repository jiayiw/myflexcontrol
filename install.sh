#!/bin/bash

echo "FlexRadio 6400 Control - Installation Script for Ubuntu Server 24.04 ARM64"
echo "======================================================================"

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    echo "Detected OS: $PRETTY_NAME"
else
    echo "Warning: Cannot detect OS version"
fi

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "Error: Please do not run this script as root"
    echo "Use sudo only for apt install commands"
    exit 1
fi

echo ""
echo "Step 1: Installing system dependencies..."
echo "You may be prompted for your password..."

sudo apt update
sudo apt install -y python3-pip python3-dev python3-venv portaudio19-dev pipewire libpipewire-0.3-dev

if [ $? -ne 0 ]; then
    echo "Error: Failed to install system dependencies"
    exit 1
fi

echo ""
echo "Step 2: Creating Python virtual environment..."

python3 -m venv venv

if [ $? -ne 0 ]; then
    echo "Error: Failed to create virtual environment"
    exit 1
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo ""
echo "Step 3: Upgrading pip..."
pip install --upgrade pip

echo ""
echo "Step 4: Installing Python packages..."

pip install PyQt6 pyqtgraph PyAudio numpy PyYAML

if [ $? -ne 0 ]; then
    echo "Error: Failed to install Python packages"
    exit 1
fi

echo ""
echo "======================================================================"
echo "Installation completed successfully!"
echo ""
echo "To run the application:"
echo "  source venv/bin/activate"
echo "  python run.py"
echo ""
echo "Or deactivate the virtual environment later:"
echo "  deactivate"
