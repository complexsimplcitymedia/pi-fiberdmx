# FIBER LASER DMX - CLIENT FIX INSTRUCTIONS

## Problem Summary
1. Touchscreen not working
2. laser-dmx.local not resolving
3. HTTPS/SSL configuration needed

## THE FIX (Simple - One Command)

Connect to your Raspberry Pi via SSH or keyboard/mouse, then run:

```bash
sudo bash /home/laser-dmx/fiber-laser-dmx/scripts/diagnose_and_fix.sh
```

This script will:
- ✓ Install touchscreen configuration
- ✓ Setup mDNS for laser-dmx.local
- ✓ Configure WiFi hotspot
- ✓ Enable HTTPS with Caddy
- ✓ Show you a complete system status

## After Running the Script

**YOU MUST REBOOT:**
```bash
sudo reboot
```

## After Reboot

### Access from Phone/Tablet:
1. Connect to WiFi network: **laser-dmx**
2. Password: **laser1234**
3. Open browser to: **https://laser-dmx.local**
4. You'll see a security warning (self-signed certificate) - click "Advanced" then "Proceed"
5. Touchscreen on the Pi should now work

### Alternative Access Methods:
- http://laser-dmx.local (if HTTPS gives issues)
- https://192.168.50.1 (direct IP)
- http://localhost:8080 (on the Pi itself)

## Troubleshooting

If touchscreen still doesn't work after reboot:
```bash
# Check if touchscreen is detected
lsusb | grep -i touch

# Check X11 is using the config
ls -la /etc/X11/xorg.conf.d/40-libinput.conf

# Restart X11 (will close all windows)
sudo systemctl restart lightdm
```

If laser-dmx.local doesn't resolve:
```bash
# Check avahi is running
sudo systemctl status avahi-daemon

# Check hostname
hostname
# Should say: laser-dmx
```

If hotspot doesn't work:
```bash
# Check hotspot status
nmcli connection show --active | grep FiberLaserHotspot

# Restart hotspot
sudo nmcli connection down FiberLaserHotspot
sudo nmcli connection up FiberLaserHotspot
```

## Contact
If issues persist, send me:
```bash
# Run this and send output:
sudo bash /home/laser-dmx/fiber-laser-dmx/scripts/diagnose_and_fix.sh > ~/diagnostic_output.txt 2>&1
cat ~/diagnostic_output.txt
```
