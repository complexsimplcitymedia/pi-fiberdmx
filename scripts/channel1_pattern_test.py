import time
from ola.ClientWrapper import ClientWrapper

# Channel 1 pattern from Laser_Master_patterns_timings.txt
# Sequence: ON/OFF durations in seconds
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

def run_pattern():
    for value, duration in pattern:
        send_dmx(value)
        time.sleep(duration)
    # Optionally, turn off at end
    send_dmx(0)

if __name__ == "__main__":
    run_pattern()
    print("Channel 1 pattern complete.")
