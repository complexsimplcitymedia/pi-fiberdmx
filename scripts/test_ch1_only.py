#!/usr/bin/env python
"""
Ultra-simple test: Flash ONLY channel 1 at 50% brightness
Everything else = 0
"""

import serial
import time
import os

def find_port():
    if os.path.exists("/dev/dmx-usb"):
        return "/dev/dmx-usb"
    for n in range(6):
        p = f"/dev/ttyUSB{n}"
        if os.path.exists(p):
            return p
    raise SystemExit("No DMX port found")

def send_frame(ser, levels):
    """Send DMX512 frame"""
    payload = bytes([0]) + bytes(levels[:512])
    ser.break_condition = True
    time.sleep(0.0001)
    ser.break_condition = False
    time.sleep(0.000012)
    ser.write(payload)

port = find_port()
ser = serial.Serial(port, baudrate=250000, bytesize=8, parity='N', stopbits=2)
print(f"Connected to {port}\n")

try:
    for i in range(10):
        # Channel 1 = 128 (50%), everything else = 0
        levels = [0] * 512
        levels[0] = 128
        send_frame(ser, levels)
        print(f"Frame {i+1}: CH1=128, rest=0")
        time.sleep(0.5)
        
        # All off
        levels = [0] * 512
        send_frame(ser, levels)
        print(f"Frame {i+1}b: All OFF")
        time.sleep(0.5)

except KeyboardInterrupt:
    print("\nStopped")
finally:
    levels = [0] * 512
    send_frame(ser, levels)
    ser.close()
