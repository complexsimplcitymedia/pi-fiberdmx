#!/bin/bash
# Quick fix script to install touchscreen configuration and restart X

echo "Installing touchscreen X11 configuration..."

# Copy touchscreen input config
sudo cp /home/laser-dmx/fiber-laser-dmx/etc/X11/xorg.conf.d/40-libinput.conf /etc/X11/xorg.conf.d/40-libinput.conf

echo "✓ Touchscreen configuration installed"
echo ""
echo "To apply changes, you need to restart X11:"
echo "  Option 1: Reboot the Pi:  sudo reboot"
echo "  Option 2: Restart X only:  sudo systemctl restart lightdm (if using lightdm)"
echo "  Option 3: Kill X and it will auto-restart"
echo ""
echo "Checking if touchscreen USB device is detected..."
lsusb | grep -i "touch\|eGalax\|FT5406\|Goodix\|ilitek" || echo "No common touchscreen devices found in lsusb"
echo ""
echo "Input devices:"
ls -la /dev/input/event* 2>/dev/null || echo "No event devices found"
