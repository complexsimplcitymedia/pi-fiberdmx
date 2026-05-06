#!/usr/bin/env python3
"""
DMX UI Kiosk Mode Launcher
Launches Chromium in full-screen kiosk mode for 800x480 display
"""
import subprocess
import time
import os

def disable_screensaver():
    """Disable screensaver and power management"""
    subprocess.run(['xset', 's', 'off'], check=False)
    subprocess.run(['xset', '-dpms'], check=False)
    subprocess.run(['xset', 's', 'noblank'], check=False)

def launch_chromium():
    """Launch Chromium in kiosk mode"""
    # Wait for display to be ready
    time.sleep(5)
    
    # Disable screensaver
    disable_screensaver()
    
    # Chromium kiosk flags for 800x480 display
    chromium_cmd = [
        '/usr/bin/chromium',
        '--kiosk',
        '--no-first-run',
        '--no-default-browser-check',
        '--disable-popup-blocking',
        '--disable-translate',
        '--disable-infobars',
        '--disable-extensions',
        '--start-fullscreen',
        '--window-size=800,480',
        '--window-position=0,0',
        '--disable-session-crashed-bubble',
        '--disable-features=TranslateUI',
        '--noerrdialogs',
        '--disable-suggestions-ui',
        '--disable-save-password-bubble',
        'http://laser-dmx.local/'
    ]
    
    # Set environment
    env = os.environ.copy()
    env['DISPLAY'] = ':0'
    env['XAUTHORITY'] = '/home/laser-dmx/.Xauthority'
    
    # Launch Chromium
    subprocess.run(chromium_cmd, env=env)

if __name__ == '__main__':
    launch_chromium()
