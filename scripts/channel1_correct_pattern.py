#!/usr/bin/env python
"""
Channel 1 Correct Pattern - Using A (Dot-Dash) from master timings
NOT the digit pattern - the fiber identification pattern
"""
import sys
import os
sys.path.insert(0, '/home/laser-dmx/fiber-laser-dmx/scripts')

from dmx_controller import DMXController
import time

# Channel 1 uses A-D-1 pattern for complete fiber identification
# Reading the ON/OFF columns correctly from Laser_Master_patterns_timings.txt:
# A: ON .12s, OFF .12s, ON .36s, OFF .84s = total 1.44s
# D: ON .36s, OFF .12s+.12s+.12s+.12s+.84s = ON .36s, OFF 1.32s = total 1.68s
# 1: ON .12s, OFF .12s, ON .36s, OFF .12s, ON .36s, OFF .12s, ON .36s, OFF .12s, ON .36s, OFF .99s = total 2.94s
pattern = [
    # A pattern (1.44s total)
    (255, 0.12),  # ON
    (0,   0.12),  # OFF
    (255, 0.36),  # ON
    (0,   0.84),  # OFF
    # D pattern (1.68s total)
    (255, 0.36),  # ON
    (0,   1.32),  # OFF (0.12+0.12+0.12+0.12+0.84)
    # 1 pattern (2.94s total)
    (255, 0.12),  # ON
    (0,   0.12),  # OFF
    (255, 0.36),  # ON
    (0,   0.12),  # OFF
    (255, 0.36),  # ON
    (0,   0.12),  # OFF
    (255, 0.36),  # ON
    (0,   0.12),  # OFF
    (255, 0.36),  # ON
    (0,   0.99)   # OFF
]

def main():
    try:
        controller = DMXController(serial_port="/dev/ttyUSB1")
        controller.connect()
        print("✓ Connected to DMX adapter")
        print("Starting Channel 1 A pattern (Dot-Dash) - Ctrl+C to stop\n")
        
        try:
            while True:
                print("Cycle:")
                for brightness, duration in pattern:
                    controller.channel_set(1, brightness)
                    levels = controller._get_dmx_levels()
                    controller.send_dmx_frame(levels)
                    status = "ON (dot/dash)" if brightness == 255 else "OFF"
                    print(f"  {status} for {duration:.2f}s")
                    time.sleep(duration)
        
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
