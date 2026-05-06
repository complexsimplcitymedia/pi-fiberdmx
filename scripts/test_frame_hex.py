#!/usr/bin/env python
"""
Ultra-precise frame test: 
- Channel 1 = 255 (full on)
- Channels 2-512 = 0 (all off)
Show hex dump of what we send
"""
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
print(f"Connected to {port}\n")

# Build frame: start code (0) + 512 channels
levels = [0] * 512
levels[0] = 255  # Channel 1 ONLY

payload = bytes([0]) + bytes(levels[:512])

print(f"Frame size: {len(payload)} bytes")
print(f"First 20 bytes (hex): {payload[:20].hex()}")
print(f"Byte 0 (start code): {payload[0]:02x}")
print(f"Byte 1 (channel 1):  {payload[1]:02x} ({payload[1]})")
print(f"Byte 2 (channel 2):  {payload[2]:02x} ({payload[2]})")
print(f"Byte 3 (channel 3):  {payload[3]:02x} ({payload[3]})")
print(f"Byte 16 (channel 15): {payload[16]:02x} ({payload[16]})")
print()

# Send it
print("Sending frame...")
ser.break_condition = True
time.sleep(0.0001)
ser.break_condition = False
time.sleep(0.000012)
written = ser.write(payload)
print(f"✓ Sent {written} bytes\n")

# Keep sending for a few seconds so you can observe
for i in range(5):
    time.sleep(0.5)
    ser.write(payload)
    print(f"Frame {i+2} sent")

ser.close()
