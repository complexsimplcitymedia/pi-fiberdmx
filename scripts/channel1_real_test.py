#!/usr/bin/env python
"""
Channel 1 Pattern Test - Using Actual DMX Serial Controller
"""
import sys

# Add scripts to path so we can import dmx_controller
sys.path.insert(0, '/home/laser-dmx/fiber-laser-dmx/scripts')

from dmx_controller import DMXController
import time

# Channel 1 pattern from Laser_Master_patterns_timings.txt
pattern = [
    (255, 0.12),  # ON for 0.12s
    (0,   0.12),  # OFF for 0.12s
    (255, 0.36),  # ON for 0.36s
    (0,   0.12),  # OFF for 0.12s
    (255, 0.36),  # ON for 0.36s
    (0,   0.12),  # OFF for 0.12s
    (255, 0.36),  # ON for 0.36s
    (0,   0.12),  # OFF for 0.12s
    (255, 0.36),  # ON for 0.36s
    (0,   0.99)   # OFF for 0.99s
]

def main():
    try:
        # Connect to DMX controller
        controller = DMXController(serial_port="/dev/ttyUSB1")
        controller.connect()
        print("✓ Connected to DMX adapter")
        print("Starting Channel 1 continuous pattern (Ctrl+C to stop)...")
        
        # Run pattern in loop until interrupted
        try:
            while True:
                for brightness, duration in pattern:
                    controller.channel_set(1, brightness)
                    levels = controller._get_dmx_levels()
                    controller.send_dmx_frame(levels)
                    time.sleep(duration)
        except KeyboardInterrupt:
            print("\n✓ Stopped by user")
        
        # Ensure OFF at end
        controller.channel_set(1, 0)
        levels = controller._get_dmx_levels()
        controller.send_dmx_frame(levels)
        print("✓ Channel 1 set to OFF.")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
