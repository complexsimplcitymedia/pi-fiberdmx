#!/bin/bash
# Boot sequence: start UI and animation together
cd /home/laser-dmx/fiber-laser-dmx

# Start DMX UI web server immediately in background
/home/laser-dmx/miniconda3/envs/fiber-laser-dmx/bin/python /home/laser-dmx/fiber-laser-dmx/ui/dmx_ui.py &

# Run boot animation on framebuffer (runs for ~20 seconds)
timeout 25 python fb_boot.py > /dev/null 2>&1

# Animation done, wait a moment for UI to be ready
sleep 2

# Launch X with just Chromium in kiosk mode (no desktop environment)
startx /usr/bin/chromium --kiosk --noerrdialogs --disable-infobars --touch-events=enabled http://laser-dmx.local -- :0 vt1
