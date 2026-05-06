#!/bin/bash
# Setup Kiosk Mode for Raspberry Pi DMX UI
# Configures the system for a dedicated display experience

echo "Setting up Kiosk Mode..."

# 1. Disable screen blanking and power management
sudo mkdir -p /etc/X11/xorg.conf.d
sudo tee /etc/X11/xorg.conf.d/90-kiosk.conf > /dev/null <<EOF
Section "ServerFlags"
    Option "BlankTime" "0"
    Option "StandbyTime" "0"
    Option "SuspendTime" "0"
    Option "OffTime" "0"
EndSection

Section "Monitor"
    Identifier "HDMI-1"
    Option "DPMS" "false"
EndSection

Section "Screen"
    Identifier "Screen0"
    Monitor "HDMI-1"
    Option "DPMS" "false"
EndSection
EOF

# 2. Create systemd user service for X11 screensaver disable
mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/disable-screensaver.service <<EOF
[Unit]
Description=Disable X11 Screensaver for Kiosk
After=display-manager.service

[Service]
Type=oneshot
Environment="DISPLAY=:0"
ExecStart=/usr/bin/xset s off
ExecStart=/usr/bin/xset -dpms
ExecStart=/usr/bin/xset s noblank
RemainAfterExit=yes

[Install]
WantedBy=graphical.target
EOF

systemctl --user enable disable-screensaver.service

# 3. Configure lightdm for auto-login (if using lightdm)
if command -v lightdm &> /dev/null; then
    echo "[SeatDefaults]
autologin-user=laser-dmx
autologin-user-timeout=0" | sudo tee -a /etc/lightdm/lightdm.conf
fi

# 4. Disable console screensaver
echo "consoleblank=0" | sudo tee -a /boot/cmdline.txt

echo "✓ Kiosk mode configuration complete"
echo "Next steps:"
echo "1. Reboot the system"
echo "2. Enable the systemd service: sudo systemctl enable dmx-ui-browser.service"
echo "3. Start the service: sudo systemctl start dmx-ui-browser.service"
