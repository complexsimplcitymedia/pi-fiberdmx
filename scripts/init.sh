#!/bin/bash
# Fiber Laser DMX System - Complete Initialization Wrapper
# Simple one-command initialization for the entire system
# NOTE: This script must be run within the fiber-laser-dmx Conda environment

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "=================================================="
echo "  Fiber Laser DMX System - Initialization"
echo "=================================================="
echo ""
echo "This script will initialize the complete system:"
echo "  • System dependencies (apt packages)"
echo "  • Miniconda3 ARM64"
echo "  • Conda environment (fiber-laser-dmx)"
echo "  • Python dependencies"
echo "  • FTDI USB-DMX udev rules"
echo "  • Systemd services"
echo "  • nginx web server setup"
echo "  • PHP-FPM configuration"
echo "  • HardInfo2 web interface setup"
echo "  • WiFi hotspot configuration"
echo "  • Caddy reverse proxy configuration"
echo ""
echo "Project root: $PROJECT_ROOT"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
   echo "This script must be run with sudo:"
   echo "  sudo $0 $@"
   exit 1
fi

# Run Python initialization script (using conda python)
exec python "$PROJECT_ROOT/scripts/init_all.py" "$@"
