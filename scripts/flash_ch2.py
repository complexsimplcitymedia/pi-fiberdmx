#!/usr/bin/env python
"""
Sequential Pattern Flash Test
Loads patterns from Laser_Master_patterns_timings.txt via dmx_patterns.py
Flashes each channel 1-12 individually in sequence
5 cycles per channel, infinite loop
"""

import serial
import time
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from dmx_patterns import PatternParser

def find_port():
    """Auto-detect DMX USB device"""
    if os.path.exists("/dev/dmx-usb"):
        return "/dev/dmx-usb"
    for n in range(6):
        p = f"/dev/ttyUSB{n}"
        if os.path.exists(p):
            return p
    raise SystemExit("No DMX USB device found")

def send_frame(ser, levels):
    """Send DMX frame with break condition"""
    payload = bytes([0] + levels[:512])
    ser.break_condition = True
    time.sleep(0.0001)      # ~100   s break
    ser.break_condition = False
    time.sleep(0.000012)    # ~12   s MAB
    ser.write(payload)

def main():
    """Run channel 2 test - continuous flashing"""

    # Connect to serial
    try:
        port = find_port()
        ser = serial.Serial(port, baudrate=250000, bytesize=8, parity='N', stopbits=2)
        print(f" ^|^s Connected to {port}")
    except Exception as e:
        print(f" ^|^w ERROR: {e}")
        return 1

    # Load patterns from file
    parser = PatternParser()
    if not parser.patterns:
        print(" ^|^w No patterns loaded")
        ser.close()
        return 1

    pattern = parser.get_pattern(1)
    if not pattern:
        print(" ^|^w No pattern for channel 1")
        ser.close()
        return 1

    cycle_time = sum(seg.duration for seg in pattern)
    print(f" ^|^s Loaded channel 1 pattern: {cycle_time:.2f}s per cycle")
    print("\n" + "="*70)
    print("CHANNEL 1 FLASH TEST - Continuous")
    print("="*70 + "\n")

    cycle_num = 0

    try:
        # Create levels array ONCE and reuse it
        levels = [0] * 512

        while True:
            cycle_num += 1
            print(f"Cycle {cycle_num}...", end=" ", flush=True)
            start = time.time()

            # Play pattern for CHANNEL 2 ONLY
            for segment in pattern:
                # Update only channel 2, keep everything else at 0
                levels[0] = 255 if segment.state == "ON" else 0
                send_frame(ser, levels)
                time.sleep(segment.duration)

            elapsed = time.time() - start
            print(f" ^|^s ({elapsed:.2f}s)")

    except KeyboardInterrupt:
        print("\n ^|^w STOPPED")
        levels = [0] * 512
        send_frame(ser, levels)
    except Exception as e:
        print(f"\n ^|^w ERROR: {e}")
        levels = [0] * 512
        send_frame(ser, levels)
    finally:
        ser.close()
        print("\nAll channels cleared")

if __name__ == "__main__":
    sys.exit(main() or 0)

