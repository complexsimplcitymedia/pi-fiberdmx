#!/usr/bin/env python3
"""
Boot animation using VLC with DRM output
Plays MP4 video directly to display
"""
import sys
import os
import subprocess
import time

# Configuration
VIDEO_FILE = '/home/laser-dmx/fiber-laser-dmx/ui/bootanimation/bootsplash800480.mp4'
PLAY_DURATION = 25  # seconds

def play_boot_animation():
    """Play boot animation using VLC with DRM/KMS video output"""

    if not os.path.exists(VIDEO_FILE):
        print(f"Error: Video file not found: {VIDEO_FILE}", file=sys.stderr)
        return

    print(f"Playing boot animation: {VIDEO_FILE}", file=sys.stderr)

    try:
        # Use VLC with DRM video output
        cmd = [
            'cvlc',  # Command-line VLC
            '--fullscreen',
            '--no-video-title-show',
            '--no-audio',
            '--loop',
            '--vout=drm_vout',  # DRM video output plugin
            VIDEO_FILE
        ]

        print("Boot animation started", file=sys.stderr)

        # Start VLC process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # Wait for specified duration
        time.sleep(PLAY_DURATION)

        # FIXED: Kill VLC more aggressively
        subprocess.run(['pkill', '-9', 'vlc'], stderr=subprocess.DEVNULL)

        # Clear framebuffer
        try:
            subprocess.run(['dd', 'if=/dev/zero', 'of=/dev/fb0'], timeout=1, stderr=subprocess.DEVNULL)
        except:
            pass

        print("Boot animation complete", file=sys.stderr)

    except Exception as e:
        print(f"Error during playback: {e}", file=sys.stderr)

if __name__ == '__main__':
    try:
        play_boot_animation()
    except Exception as e:
        print(f"Boot animation error: {e}", file=sys.stderr)
        sys.exit(1)
