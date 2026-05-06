#!/bin/bash
# Setup WiFi hotspot on wlan0 (internal WiFi)
# This creates a persistent hotspot that devices can connect to

INTERFACE="wlan0"
SSID="laser-dmx"
PASSWORD="laser1234"
CONNECTION_NAME="FiberLaserHotspot"

echo "Setting up WiFi hotspot on $INTERFACE..."

# Remove any existing hotspot connection
sudo nmcli connection delete "$CONNECTION_NAME" 2>/dev/null

# Create a new hotspot (AP mode) connection
sudo nmcli connection add \
    type wifi \
    ifname "$INTERFACE" \
    con-name "$CONNECTION_NAME" \
    autoconnect yes \
    ssid "$SSID" \
    mode ap \
    wifi-sec.key-mgmt wpa-psk \
    wifi-sec.psk "$PASSWORD" \
    ipv4.method shared \
    ipv4.addresses "192.168.50.1/24"

# Activate the connection
sudo nmcli connection up "$CONNECTION_NAME"

echo "WiFi hotspot created!"
echo "SSID: $SSID"
echo "Password: $PASSWORD"
echo "IP: 192.168.50.1"
