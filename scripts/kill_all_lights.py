#!/usr/bin/env python
"""KILL ALL LIGHTS - Send all zeros"""
import serial
import os
import time

def find_port():
    if os.path.exists("/dev/dmx-usb"):
        return "/dev/dmx-usb"
    for n in range(6):
        p = f"/dev/ttyUSB{n}"
        if os.path.exists(p):
            return p
    raise SystemExit("No DMX port found")

port = find_port()
ser = serial.Serial(port, baudrate=250000, bytesize=8, parity='N', stopbits=2)

# All zeros - everything OFF
levels = [0] * 512
payload = bytes([0]) + bytes(levels[:512])

ser.break_condition = True
time.sleep(0.0001)
ser.break_condition = False
time.sleep(0.000012)
ser.write(payload)

print("✓ ALL LIGHTS KILLED")
ser.close()
