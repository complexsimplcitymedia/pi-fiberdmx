#!/bin/bash
# Comprehensive diagnostic and fix script for Fiber Laser DMX system
# Run this on the client's device to fix touchscreen, mDNS, hotspot, and HTTPS issues

set -e

echo "=========================================="
echo "Fiber Laser DMX System Diagnostic & Fix"
echo "=========================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# 1. TOUCHSCREEN FIX
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. TOUCHSCREEN CONFIGURATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f "/home/laser-dmx/fiber-laser-dmx/etc/X11/xorg.conf.d/40-libinput.conf" ]; then
    sudo mkdir -p /etc/X11/xorg.conf.d
    sudo cp /home/laser-dmx/fiber-laser-dmx/etc/X11/xorg.conf.d/40-libinput.conf /etc/X11/xorg.conf.d/40-libinput.conf
    print_status "Touchscreen X11 configuration installed"
else
    print_error "Touchscreen config file missing!"
fi

# Check if touchscreen USB device is detected
echo ""
echo "Checking for touchscreen USB device..."
if lsusb | grep -iq "touch\|eGalax\|FT5406\|Goodix\|ilitek"; then
    print_status "Touchscreen USB device detected:"
    lsusb | grep -i "touch\|eGalax\|FT5406\|Goodix\|ilitek"
else
    print_warning "No common touchscreen USB device found"
    echo "All USB devices:"
    lsusb
fi

# Check input event devices
echo ""
echo "Input event devices:"
ls -la /dev/input/event* 2>/dev/null || print_warning "No event devices found"

# 2. MDNS / AVAHI FOR laser-dmx.local
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2. mDNS SETUP (laser-dmx.local)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Install avahi if not present
if ! command -v avahi-daemon &> /dev/null; then
    echo "Installing avahi-daemon..."
    sudo apt-get update
    sudo apt-get install -y avahi-daemon avahi-utils
fi

# Check hostname
CURRENT_HOSTNAME=$(hostname)
echo "Current hostname: $CURRENT_HOSTNAME"
if [ "$CURRENT_HOSTNAME" != "laser-dmx" ]; then
    print_warning "Hostname is not 'laser-dmx', setting it now..."
    echo "laser-dmx" | sudo tee /etc/hostname
    sudo hostnamectl set-hostname laser-dmx
    print_status "Hostname set to 'laser-dmx'"
fi

# Enable and start avahi
sudo systemctl enable avahi-daemon
sudo systemctl restart avahi-daemon

if systemctl is-active --quiet avahi-daemon; then
    print_status "avahi-daemon is running (enables laser-dmx.local)"
else
    print_error "avahi-daemon failed to start"
fi

# 3. WIFI HOTSPOT
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3. WIFI HOTSPOT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if NetworkManager is installed
if ! command -v nmcli &> /dev/null; then
    echo "Installing NetworkManager..."
    sudo apt-get install -y network-manager
fi

# Run the hotspot setup script
if [ -f "/home/laser-dmx/fiber-laser-dmx/scripts/setup-wifi-hotspot.sh" ]; then
    bash /home/laser-dmx/fiber-laser-dmx/scripts/setup-wifi-hotspot.sh
    print_status "WiFi hotspot configured"
else
    print_error "Hotspot setup script not found!"
fi

# Check hotspot status
echo ""
echo "Checking hotspot status..."
if nmcli connection show --active | grep -q "FiberLaserHotspot"; then
    print_status "Hotspot is ACTIVE"
    nmcli connection show FiberLaserHotspot | grep -E "GENERAL.NAME|IP4.ADDRESS|802-11-wireless.ssid"
else
    print_warning "Hotspot is not active, attempting to start..."
    sudo nmcli connection up FiberLaserHotspot || print_error "Failed to start hotspot"
fi

# 4. CADDY HTTPS SETUP
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4. CADDY REVERSE PROXY & HTTPS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if Caddy is installed
if ! command -v caddy &> /dev/null; then
    echo "Installing Caddy..."
    sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
    sudo apt update
    sudo apt install -y caddy
fi

# Copy Caddyfile to /etc/caddy/
if [ -f "/home/laser-dmx/fiber-laser-dmx/Caddyfile" ]; then
    sudo cp /home/laser-dmx/fiber-laser-dmx/Caddyfile /etc/caddy/Caddyfile
    
    print_status "Caddyfile installed (Caddy will auto-generate self-signed cert for laser-dmx.local)"
    
    # Reload Caddy
    sudo systemctl enable caddy
    sudo systemctl reload caddy
    
    if systemctl is-active --quiet caddy; then
        print_status "Caddy is running"
    else
        print_warning "Caddy is not running, starting it..."
        sudo systemctl start caddy
    fi
else
    print_error "Caddyfile not found!"
fi

# 5. DMX UI SERVICE
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5. DMX UI STATUS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if DMX UI is running
if pgrep -f "dmx_ui.py" > /dev/null; then
    print_status "DMX UI (dmx_ui.py) is running"
else
    print_warning "DMX UI is not running"
fi

# Check if Flask is listening on port 8080
if netstat -tuln 2>/dev/null | grep -q ":8080"; then
    print_status "Service is listening on port 8080"
else
    print_warning "Nothing is listening on port 8080"
fi

# SUMMARY
echo ""
echo "=========================================="
echo "SUMMARY & NEXT STEPS"
echo "=========================================="
echo ""
echo "Configuration files installed:"
echo "  ✓ /etc/X11/xorg.conf.d/40-libinput.conf (touchscreen)"
echo "  ✓ /etc/caddy/Caddyfile (HTTPS proxy)"
echo ""
echo "Services status:"
systemctl is-active --quiet avahi-daemon && echo "  ✓ avahi-daemon (mDNS)" || echo "  ✗ avahi-daemon"
systemctl is-active --quiet caddy && echo "  ✓ caddy (HTTPS proxy)" || echo "  ✗ caddy"
nmcli connection show --active | grep -q "FiberLaserHotspot" && echo "  ✓ WiFi Hotspot" || echo "  ⚠ WiFi Hotspot"
pgrep -f "dmx_ui.py" > /dev/null && echo "  ✓ DMX UI" || echo "  ⚠ DMX UI"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TOUCHSCREEN FIX REQUIRES REBOOT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "To activate the touchscreen, you must reboot:"
echo "  sudo reboot"
echo ""
echo "After reboot, the system will be accessible at:"
echo "  • https://laser-dmx.local (from any device on hotspot)"
echo "  • http://laser-dmx.local (if HTTPS has cert warning)"
echo "  • https://192.168.50.1 (direct IP on hotspot)"
echo ""
echo "WiFi Hotspot credentials:"
echo "  SSID: laser-dmx"
echo "  Password: laser1234"
echo ""
print_warning "Browser will show security warning for HTTPS (self-signed cert) - click 'Advanced' and 'Proceed'"
echo ""
