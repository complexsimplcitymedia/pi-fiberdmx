#!/usr/bin/env python3
"""
RUN MORSE PATTERNS - Execute the exact timing sequences
Coordinates with remote Claude's timing work
"""

import sys
import os
import time
import serial
import serial.tools.list_ports

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def find_dmx_port():
    """Find DMX adapter port"""
    ports = ['/dev/ttyUSB0', '/dev/ttyUSB1', '/dev/ttyACM0']
    for port in ports:
        if os.path.exists(port):
            return port

    # Try to detect
    for port in serial.tools.list_ports.comports():
        if 'FTDI' in port.description or 'USB' in port.description:
            return port.device

    return None

def send_dmx_frame(ser, channels):
    """Send DMX512 frame"""
    try:
        ser.break_condition = True
        time.sleep(0.0001)
        ser.break_condition = False
        time.sleep(0.000012)
        ser.write(bytes([0] + channels[:512]))
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def run_morse_sequence(ser, channel, pattern_name, timings):
    """
    Run a Morse code pattern on a channel
    timings: list of (state, duration) tuples
    state: "ON" or "OFF"
    duration: seconds (float)
    """
    print(f"\n🎯 Running pattern '{pattern_name}' on channel {channel}")
    print(f"   Sequence: {len(timings)} segments")

    channels = [0] * 512

    for i, (state, duration) in enumerate(timings):
        if state == "ON":
            channels[channel - 1] = 255
            symbol = "▓"
        else:
            channels[channel - 1] = 0
            symbol = "░"

        send_dmx_frame(ser, channels)
        print(f"   {i+1:2d}. {symbol} {state:3s} {duration:.3f}s", flush=True)
        time.sleep(duration)

    # Final OFF
    channels[channel - 1] = 0
    send_dmx_frame(ser, channels)
    print("   ✅ Pattern complete")

def parse_timing_string(timing_str):
    """
    Parse timing string like ".12s,.12s,.36s,.84s"
    Returns list of (state, duration) starting with ON
    """
    timings = []
    parts = timing_str.replace('s', '').split(',')

    # Patterns start with ON
    on = True
    for part in parts:
        duration = float(part)
        timings.append(("ON" if on else "OFF", duration))
        on = not on

    return timings

def load_pattern_from_file(channel):
    """Load pattern timing from Laser_Master_patterns_timings.txt"""
    patterns_file = "/home/laser-dmx/fiber-laser-dmx/data/Laser_Master_patterns_timings.txt"

    if not os.path.exists(patterns_file):
        # Try alternate paths
        alt_paths = [
            "../data/Laser_Master_patterns_timings.txt",
            "../../data/Laser_Master_patterns_timings.txt",
            "/home/pi/fiber-laser-dmx/data/Laser_Master_patterns_timings.txt"
        ]
        for path in alt_paths:
            if os.path.exists(path):
                patterns_file = path
                break

    if not os.path.exists(patterns_file):
        print("⚠️  Pattern file not found")
        return None

    print(f"📖 Loading patterns from: {patterns_file}")

    # Read and parse the file
    with open(patterns_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or not line[0].isdigit():
                continue

            # Parse: "1. A .12s,.12s,.36s,.84s - D .36s,.12s,.12s,.12s,.12s,.84s - 1 .12s,.12s,.36s,..."
            parts = line.split('.')
            if len(parts) < 2:
                continue

            ch_num = int(parts[0].strip())
            if ch_num != channel:
                continue

            # Found the channel - parse all three parts (A + strand + digit)
            # Extract timings between "A" and "-", between first "-" and second "-", after second "-"
            rest = '.'.join(parts[1:])

            # Split by '-' to get A, strand, and digit sections
            sections = rest.split('-')
            if len(sections) < 3:
                continue

            a_section = sections[0].strip()
            strand_section = sections[1].strip()
            digit_section = sections[2].strip()

            # Extract timing strings (everything after the letter/digit identifier)
            import re

            a_match = re.search(r'A\s+([\d.,s]+)', a_section)
            strand_match = re.search(r'[DGU]\s+([\d.,s]+)', strand_section)
            digit_match = re.search(r'\d+\s+([\d.,s]+)', digit_section)

            if not (a_match and strand_match and digit_match):
                continue

            # Combine all timings
            combined_timing = a_match.group(1) + ',' + strand_match.group(1) + ',' + digit_match.group(1)

            # Get pattern name
            strand_letter = re.search(r'([DGU])', strand_section).group(1)
            digit_num = re.search(r'(\d+)', digit_section).group(1)
            pattern_name = f"A-{strand_letter}-{digit_num}"

            return pattern_name, combined_timing

    return None

def main():
    print("="*70)
    print("🎯 MORSE PATTERN EXECUTOR - Running Exact Timings")
    print("="*70)

    # Find DMX port
    dmx_port = find_dmx_port()
    if not dmx_port:
        print("❌ No DMX adapter found!")
        return

    print(f"📡 DMX Port: {dmx_port}")

    # Connect
    try:
        ser = serial.Serial(
            dmx_port,
            baudrate=250000,
            bytesize=8,
            parity='N',
            stopbits=2,
            timeout=1
        )
        print("✅ Connected to DMX adapter")

        # Clear all channels
        channels = [0] * 512
        send_dmx_frame(ser, channels)
        time.sleep(0.5)

        # Run patterns for channels 1-12
        print("\n" + "="*70)
        print("🚀 EXECUTING MORSE SEQUENCES")
        print("="*70)

        for channel in range(1, 13):
            result = load_pattern_from_file(channel)

            if result:
                pattern_name, timing_str = result
                timings = parse_timing_string(timing_str)
                run_morse_sequence(ser, channel, pattern_name, timings)
                time.sleep(1)  # Pause between patterns
            else:
                print(f"\n⚠️  Channel {channel}: No pattern found")

        # Final cleanup
        print("\n" + "="*70)
        channels = [0] * 512
        send_dmx_frame(ser, channels)
        print("✅ All patterns executed, channels cleared")
        print("="*70)

        ser.close()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

