#!/bin/bash
# DMX UI Kiosk Mode Launcher
# Launches Chromium in full-screen kiosk mode

# Wait for display to be ready
sleep 2

# Disable screensaver and power management
xset s off
xset -dpms
xset s noblank

# Launch Chromium in kiosk mode
/usr/bin/chromium-browser \
  --kiosk \
  --no-first-run \
  --no-default-browser-check \
  --disable-popup-blocking \
  --disable-translate \
  --disable-infobars \
  --disable-extensions \
  --start-fullscreen \
  http://laser-dmx.local/
