#!/bin/bash

# ==============================================================================
# Boot Animation Setup Script
# Installs and configures mpv-based boot splash screen for Raspberry Pi 5
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BOOTANIM_DIR="$PROJECT_ROOT/ui/bootanimation"
VIDEO_FILE="$BOOTANIM_DIR/bootsplash.mp4"
SERVICE_FILE="/etc/systemd/system/boot-animation.service"
WRAPPER_SCRIPT="/usr/local/bin/boot-animation.sh"

echo "=== Boot Animation Setup for Raspberry Pi 5 ==="
echo ""

# Step 1: Verify video file exists
echo "[1/6] Checking boot animation video..."
if [ ! -f "$VIDEO_FILE" ]; then
    echo "ERROR: Video file not found at $VIDEO_FILE"
    exit 1
fi
echo "✓ Video file found: $VIDEO_FILE"
echo ""

# Step 2: Install mpv
echo "[2/6] Installing mpv video player..."
if ! command -v mpv &> /dev/null; then
    sudo apt-get update > /dev/null 2>&1
    sudo apt-get install -y mpv > /dev/null 2>&1
    echo "✓ mpv installed successfully"
else
    echo "✓ mpv already installed"
fi
echo ""

# Step 3: Create boot animation wrapper script
echo "[3/6] Creating boot animation wrapper script..."
sudo tee "$WRAPPER_SCRIPT" > /dev/null << 'EOF'
#!/bin/bash

# Boot Animation Wrapper Script
# Plays video during early boot with proper error handling

VIDEO="/home/laser-dmx/fiber-laser-dmx/ui/bootanimation/bootsplash.mp4"
LOGFILE="/var/log/boot-animation.log"

{
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting boot animation"
    
    # Check if video file exists
    if [ ! -f "$VIDEO" ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: Video file not found at $VIDEO"
        exit 1
    fi
    
    # Play video with mpv
    # --no-config: don't load user mpv config
    # --fullscreen: fullscreen video
    # --no-audio: disable audio (optional, comment out if you want sound)
    # --force-window: create window even without display manager
    # --autofit=100%: scale to 100% of display
    # --fs-screen=current: use current screen
    mpv --no-config \
        --fullscreen \
        --no-audio \
        --force-window \
        --autofit=100% \
        --fs-screen=current \
        "$VIDEO" 2>&1
    
    EXIT_CODE=$?
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Boot animation exited with code $EXIT_CODE"
    
} >> "$LOGFILE" 2>&1

exit 0
EOF

sudo chmod +x "$WRAPPER_SCRIPT"
echo "✓ Wrapper script created at $WRAPPER_SCRIPT"
echo ""

# Step 4: Create systemd service
echo "[4/6] Creating systemd boot animation service..."
sudo tee "$SERVICE_FILE" > /dev/null << EOF
[Unit]
Description=Raspberry Pi Boot Animation Splash Screen
Before=getty@tty1.service
After=local-fs-target.target
ConditionVirtualization=!container

[Service]
Type=simple
User=root
ExecStart=$WRAPPER_SCRIPT
StandardOutput=journal
StandardError=journal
TimeoutStartSec=30
Environment="DISPLAY=:0"
Environment="XAUTHORITY=/root/.Xauthority"

[Install]
WantedBy=multi-user.target
EOF

echo "✓ Systemd service created at $SERVICE_FILE"
echo ""

# Step 5: Enable and load service
echo "[5/6] Enabling systemd service..."
sudo systemctl daemon-reload
sudo systemctl enable boot-animation.service
echo "✓ Boot animation service enabled"
echo ""

# Step 6: Verify installation
echo "[6/6] Verifying installation..."
echo "    Video file: $(test -f "$VIDEO" && echo '✓ Found' || echo '✗ Missing')"
echo "    mpv player: $(command -v mpv > /dev/null && echo '✓ Installed' || echo '✗ Not found')"
echo "    Wrapper script: $(test -x "$WRAPPER_SCRIPT" && echo '✓ Executable' || echo '✗ Not found')"
echo "    Systemd service: $(test -f "$SERVICE_FILE" && echo '✓ Installed' || echo '✗ Not found')"
echo "    Service enabled: $(systemctl is-enabled boot-animation.service 2>/dev/null && echo '✓ Yes' || echo '✗ No')"
echo ""

echo "=== Boot Animation Setup Complete ==="
echo ""
echo "Next boot: The boot splash video will play automatically"
echo ""
echo "To test boot animation (requires reboot):"
echo "    sudo reboot"
echo ""
echo "To disable boot animation temporarily:"
echo "    sudo systemctl disable boot-animation.service"
echo "    sudo reboot"
echo ""
echo "To re-enable boot animation:"
echo "    sudo systemctl enable boot-animation.service"
echo "    sudo reboot"
echo ""
echo "To view boot animation logs:"
echo "    tail -f /var/log/boot-animation.log"
echo ""
echo "Status: $(systemctl is-active boot-animation.service || echo 'Not running (will start at next boot)')"
