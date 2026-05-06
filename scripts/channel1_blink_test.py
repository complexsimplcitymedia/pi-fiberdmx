"""
Channel 1 DMX Pattern Test Script
- Sends ON/OFF pattern for channel 1 using OLA (Open Lighting Architecture)
- Timings match Laser_Master_patterns_timings.txt
- Compatible with Conda environment
"""
import time
try:
    from ola.ClientWrapper import ClientWrapper
except ImportError:
    print("OLA Python API not found. Please install ola-python and ensure olad is running.")
    exit(1)

# Channel 1 pattern: ON/OFF durations in seconds
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

UNIVERSE = 0  # Change if your setup uses a different universe
CHANNEL = 0   # DMX channel 1 (0-indexed for OLA)

wrapper = ClientWrapper()
client = wrapper.Client()

def send_dmx(value):
    data = [0]*512
    data[CHANNEL] = value
    client.SendDmx(UNIVERSE, bytearray(data), lambda state: None)
    print(f"Sent value {value} to channel 1")

def run_pattern():
    print("Starting Channel 1 DMX pattern test...")
    for value, duration in pattern:
        send_dmx(value)
        time.sleep(duration)
    # Ensure channel is OFF at end
    send_dmx(0)
    print("Pattern complete. Channel 1 set to OFF.")

if __name__ == "__main__":
    run_pattern()
