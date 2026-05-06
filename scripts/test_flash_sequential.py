#!/usr/bin/env python
"""
Sequential Pattern Flash Test
Each channel 1-12 flashes individually (5 cycles), then moves to next
No overlapping - completely sequential
Infinite loop for camera testing
"""

import serial
import time
import os
import sys
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent))
from dmx_patterns import PatternParser

def find_port():
    """Find FTDI DMX adapter"""
    if os.path.exists("/dev/dmx-usb"):
        return "/dev/dmx-usb"
    for n in range(6):
        p = f"/dev/ttyUSB{n}"
        if os.path.exists(p):
            return p
    raise SystemExit("No DMX USB device found")

def send_frame(ser, levels):
    """Send DMX frame with break condition"""
    frame = bytes([0]*513)  # 1 start + 512 channels
    frame = frame[:1] + bytes(levels)
    ser.break_condition = True
    time.sleep(0.0001)  # 100 µs break
    ser.break_condition = False
    ser.write(frame)

# Connect
port = find_port()
ser = serial.Serial(port, baudrate=250000, bytesize=8, parity='N', stopbits=2)
print(f"✓ Connected to {port}\n")

# Load patterns
parser = PatternParser()
print(f"✓ Loaded {len(parser.patterns)} patterns\n")

LEVEL_ON = 255
LEVEL_OFF = 0
loop_num = 0

try:
    while True:
        loop_num += 1
        print(f"\n{'='*70}")
        print(f"LOOP {loop_num}")
        print(f"{'='*70}\n")
        
        # Each channel 1-12, one at a time
        for channel in range(1, 13):
            pattern = parser.get_pattern(channel)
            if not pattern:
                print(f"CH {channel:2d}: No pattern")
                continue
            
            cycle_time = sum(seg.duration for seg in pattern)
            print(f"CH {channel:2d}: {cycle_time:.2f}s pattern × 5 cycles")
            
            # 5 cycles
            for cycle in range(1, 6):
                print(f"        Cycle {cycle}/5...", end=" ", flush=True)
                cycle_start = time.time()
                
                # Play entire pattern for this channel
                for segment in pattern:
                    levels = [0] * 512
                    levels[channel - 1] = LEVEL_ON if segment.state == "ON" else LEVEL_OFF
                    send_frame(ser, levels)
                    time.sleep(segment.duration)
                
                elapsed = time.time() - cycle_start
                print(f"✓ ({elapsed:.2f}s)")
            
            # Clear this channel and wait before next
            levels = [0] * 512
            send_frame(ser, levels)
            time.sleep(0.2)
            print()
        
        print(f"Loop {loop_num} complete")

except KeyboardInterrupt:
    print("\n✗ Stopped by user")
    levels = [0] * 512
    send_frame(ser, levels)
finally:
    ser.close()
    print("All channels cleared")
