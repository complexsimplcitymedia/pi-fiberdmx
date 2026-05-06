#!/usr/bin/env python
"""
Channel 1 Pattern Diagnostic - Shows exact timing and values being sent
"""
import sys
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
        controller = DMXController(serial_port="/dev/ttyUSB1")
        controller.connect()
        print("✓ Connected to DMX adapter\n")
        
        # Run ONE cycle and show exact timing
        print("ONE PATTERN CYCLE:")
        print("-" * 60)
        start_time = time.time()
        
        for step, (brightness, duration) in enumerate(pattern, 1):
            controller.channel_set(1, brightness)
            levels = controller._get_dmx_levels()
            controller.send_dmx_frame(levels)
            
            elapsed = time.time() - start_time
            status = "ON " if brightness == 255 else "OFF"
            print(f"Step {step:2d}: {status} for {duration:.2f}s  (elapsed: {elapsed:.3f}s)")
            time.sleep(duration)
        
        elapsed = time.time() - start_time
        print("-" * 60)
        print(f"Total cycle time: {elapsed:.3f}s")
        print(f"Expected cycle time: {sum(d for _, d in pattern):.3f}s")
        
        # Turn OFF
        controller.channel_set(1, 0)
        levels = controller._get_dmx_levels()
        controller.send_dmx_frame(levels)
        print("✓ Pattern cycle complete. Channel 1 OFF.")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
