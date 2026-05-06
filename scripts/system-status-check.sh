#!/bin/bash
# System Status Check for Fiber Laser DMX

echo "╔════════════════════════════════════════════════════════════╗"
echo "║        FIBER LASER DMX - SYSTEM STATUS CHECK              ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# WiFi Check
echo "📡 WiFi Configuration:"
echo "─────────────────────────"
nmcli device status | grep -E "wlan0|wlan1" | while read line; do
    echo "  $line"
done
echo ""

# Hotspot Check
echo "🔴 WiFi Hotspot (CRITICAL):"
echo "─────────────────────────"
if nmcli connection show FiberLaserHotspot &>/dev/null; then
    SSID=$(nmcli connection show FiberLaserHotspot | grep "802-11-wireless.ssid:" | awk '{print $2}')
    echo "  ✓ Hotspot Active"
    echo "  SSID: $SSID"
    echo "  IP: 192.168.50.1/24"
else
    echo "  ✗ Hotspot NOT configured"
fi
echo ""

# Systemd Services Check
echo "🔧 System Services:"
echo "─────────────────────────"
systemctl is-active --quiet wifi-hotspot.service && echo "  ✓ WiFi Hotspot Service: ACTIVE" || echo "  ✗ WiFi Hotspot Service: INACTIVE"
systemctl is-active --quiet caddy.service && echo "  ✓ Caddy Service: ACTIVE" || echo "  ✗ Caddy Service: INACTIVE"
echo ""

# Docker Containers Check
echo "🐳 Docker Containers:"
echo "─────────────────────────"
if command -v docker &>/dev/null; then
    RUNNING=$(docker ps -q | wc -l)
    echo "  Running containers: $RUNNING"
    docker ps --format "table {{.Names}}\t{{.Status}}" 2>/dev/null | while read line; do
        echo "  $line"
    done
else
    echo "  ✗ Docker not installed"
fi
echo ""

# Listening Ports Check
echo "🌐 Listening Services:"
echo "─────────────────────────"
echo "  Port 80   (HTTP/Caddy):     $(sudo lsof -i :80 -sTCP:LISTEN -t 2>/dev/null | head -1 && echo 'LISTENING' || echo 'NOT LISTENING')"
echo "  Port 443  (HTTPS/Caddy):    $(sudo lsof -i :443 -sTCP:LISTEN -t 2>/dev/null | head -1 && echo 'LISTENING' || echo 'NOT LISTENING')"
echo "  Port 8888 (HardInfo2):      $(sudo lsof -i :8888 -sTCP:LISTEN -t 2>/dev/null | head -1 && echo 'LISTENING' || echo 'NOT LISTENING')"
echo "  Port 9443 (Portainer):      $(sudo lsof -i :9443 -sTCP:LISTEN -t 2>/dev/null | head -1 && echo 'LISTENING' || echo 'NOT LISTENING')"
echo "  Port 3306 (MariaDB):        $(sudo lsof -i :3306 -sTCP:LISTEN -t 2>/dev/null | head -1 && echo 'LISTENING' || echo 'NOT LISTENING')"
echo ""

echo "╔════════════════════════════════════════════════════════════╗"
echo "║                    CHECK COMPLETE                          ║"
echo "╚════════════════════════════════════════════════════════════╝"
