#!/usr/bin/env python3
"""
Channel 1 High-Precision Pattern - Fixed-rate DMX frames with exact timing
Sends DMX at 30Hz (33.33ms per frame) with precise ON/OFF transitions
"""

import sys
sys.path.insert(0, '/home/laser-dmx/fiber-laser-dmx/scripts')

from dmx_controller import DMXController
import time

# Channel 1 pattern from Laser_Master_patterns_timings.txt
# A + D + 1 pattern
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

DMX_FRAME_RATE = 30  # Hz (33.33ms per frame) - DMX512 standard
FRAME_TIME = 1.0 / DMX_FRAME_RATE

def main():
    try:
        controller = DMXController(serial_port="/dev/ttyUSB1")
        controller.connect()
        print(f"✓ Connected to DMX adapter (sending at {DMX_FRAME_RATE}Hz)\n")
        print("Starting Channel 1 continuous pattern (Ctrl+C to stop)...")

        try:
            while True:
                for brightness, duration in pattern:
                    # Set the brightness value
                    controller.channel_set(1, brightness)

                    # Calculate how many frames this duration spans
                    elapsed = 0.0
                    frame_start = time.time()

                    while elapsed < duration:
                        # Send DMX frame
                        levels = controller._get_dmx_levels()
                        controller.send_dmx_frame(levels)

                        # Sleep for exact frame time
                        elapsed = time.time() - frame_start
                        remaining = duration - elapsed

                        if remaining > FRAME_TIME:
                            time.sleep(FRAME_TIME)
                        else:
                            time.sleep(max(0, remaining))
                            break

        except KeyboardInterrupt:
            print("\n✓ Stopped by user")

        # Turn OFF
        controller.channel_set(1, 0)
        levels = controller._get_dmx_levels()
        controller.send_dmx_frame(levels)
        print("✓ Channel 1 set to OFF.")

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

