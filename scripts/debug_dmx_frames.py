#!/usr/bin/env python
"""
Debug: Show exactly what's being sent to DMX for each frame
"""

import serial
import time
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from dmx_patterns import PatternParser

def find_port():
    if os.path.exists("/dev/dmx-usb"):
        return "/dev/dmx-usb"
    for n in range(6):
        p = f"/dev/ttyUSB{n}"
        if os.path.exists(p):
            return p
    raise SystemExit("No DMX port found")

def send_frame(ser, levels):
    """Send DMX frame and show what we're sending"""
    payload = bytes([0]) + bytes(levels[:512])
    ser.break_condition = True
    time.sleep(0.0001)
    ser.break_condition = False
    time.sleep(0.000012)
    ser.write(payload)
    return payload

port = find_port()
ser = serial.Serial(port, baudrate=250000, bytesize=8, parity='N', stopbits=2)
print(f"Connected to {port}\n")

parser = PatternParser()
pattern = parser.get_pattern(1)

print(f"Pattern has {len(pattern)} segments\n")

try:
    cycle = 0
    for segment in pattern[:6]:  # Just first 6 segments for debugging
        cycle += 1
        levels = [0] * 512
        levels[0] = 255 if segment.state == "ON" else 0
        
        # Kill channels 2-15 explicitly
        for ch in range(1, 15):
            levels[ch] = 0
        
        payload = send_frame(ser, levels)
        
        # Show first 20 channels
        ch_status = []
        for i in range(16):
            ch_status.append(f"CH{i+1:2d}={payload[i+1]:3d}")
        
        print(f"Segment {cycle}: {segment.state:3s} {segment.duration:.2f}s - " + ", ".join(ch_status))
        time.sleep(segment.duration)

except KeyboardInterrupt:
    print("\nStopped")
finally:
    levels = [0] * 512
    send_frame(ser, levels)
    ser.close()
