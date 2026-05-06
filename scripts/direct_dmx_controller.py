#!/usr/bin/env python3
"""
Direct DMX Controller for Fiber Laser Timings
NO QLC BULLSHIT - just precise timing control with exact Morse code patterns.
Uses REAL DMX protocol via /dev/ttyUSB0 FTDI adapter.
"""

import json
import serial
import time
import sys
import threading
from typing import List, Dict
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data"
PATTERNS_FILE = DATA_DIR / "patterns.json"
TIMINGS_FILE = DATA_DIR / "Laser_Master_patterns_timings.txt"

# DMX Hardware config
DMX_DEVICE = "/dev/ttyUSB0"
DMX_BAUDRATE = 250000  # Standard DMX512 baud rate
DMX_CHANNELS = 512


class DMXController:
    """Direct DMX512 controller with precise timing"""

    def __init__(self, port: str = DMX_DEVICE):
        self.port = port
        self.ser = None
        self.dmx_levels = [0] * DMX_CHANNELS  # 512 channels
        self.lock = threading.Lock()
        self.running = False

    def connect(self):
        """Open serial connection to FTDI DMX adapter"""
        try:
            self.ser = serial.Serial(
                self.port,
                baudrate=DMX_BAUDRATE,
                bytesize=8,
                parity=serial.PARITY_NONE,
                stopbits=2,
                timeout=0,
            )
            print(f"✓ DMX connected: {self.port}")
            self.running = True
            # Start continuous DMX output thread
            threading.Thread(target=self._dmx_output_loop, daemon=True).start()
        except Exception as e:
            print(f"✗ DMX connection failed: {e}")
            raise

    def _send_dmx_frame(self):
        """Send one DMX512 frame with proper break/MAB timing"""
        if not self.ser:
            return

        try:
            # BREAK: 88-176 microseconds low
            self.ser.break_condition = True
            time.sleep(0.000176)  # 176 microseconds

            # MARK AFTER BREAK (MAB): 8-16 microseconds high
            self.ser.break_condition = False
            time.sleep(0.000012)  # 12 microseconds

            # START CODE (0x00) + 512 channel values
            with self.lock:
                frame = bytes([0] + self.dmx_levels[:DMX_CHANNELS])

            self.ser.write(frame)

        except Exception as e:
            print(f"DMX frame error: {e}")

    def _dmx_output_loop(self):
        """Continuous DMX output at ~44Hz (standard DMX refresh rate)"""
        while self.running:
            self._send_dmx_frame()
            time.sleep(0.023)  # ~44Hz refresh rate

    def set_channel(self, channel: int, value: int):
        """Set DMX channel (1-512) to value (0-255)"""
        if not 1 <= channel <= DMX_CHANNELS:
            raise ValueError(f"Channel must be 1-{DMX_CHANNELS}")
        if not 0 <= value <= 255:
            raise ValueError("Value must be 0-255")

        with self.lock:
            self.dmx_levels[channel - 1] = value

    def all_off(self):
        """Turn all channels off"""
        with self.lock:
            self.dmx_levels = [0] * DMX_CHANNELS

    def close(self):
        """Close DMX connection"""
        self.running = False
        if self.ser:
            self.all_off()
            time.sleep(0.1)
            self.ser.close()
            print("✓ DMX disconnected")


class PatternPlayer:
    """Plays timing patterns with microsecond precision"""

    def __init__(self, dmx: DMXController):
        self.dmx = dmx
        self.patterns = self._load_patterns()
        self.master_timings = self._load_master_timings()

    def _load_patterns(self) -> Dict:
        """Load Morse code patterns from JSON"""
        with open(PATTERNS_FILE, "r") as f:
            return json.load(f)

    def _load_master_timings(self) -> Dict[int, List]:
        """Parse the master timing file for channels 1-12"""
        timings = {}
        try:
            with open(TIMINGS_FILE, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or not line[0].isdigit():
                        continue

                    # Parse: " 1. A .12s,.12s,.36s,.84s - D .36s,... - 1 .12s,..."
                    parts = line.split("-")
                    if len(parts) < 3:
                        continue

                    # Extract channel number
                    channel_match = parts[0].split(".")[0].strip()
                    try:
                        channel = int(channel_match)
                    except:
                        continue

                    # Extract all timing values
                    import re

                    all_timings = re.findall(r"\.(\d+)s", line)

                    # Convert to ON/OFF pattern (starts with ON)
                    pattern = []
                    for i, val in enumerate(all_timings):
                        duration = float(f"0.{val}")
                        state = "ON" if i % 2 == 0 else "OFF"
                        pattern.append([state, duration])

                    timings[channel] = pattern
        except Exception as e:
            print(f"Warning: Could not load master timings: {e}")

        return timings

    def play_pattern(self, pattern_key: str, channel: int, loops: int = 1):
        """Play a pattern on a channel with exact timing"""
        pattern_key = pattern_key.upper()

        # Try master timings first (for channels 1-12)
        if isinstance(pattern_key, str) and pattern_key.isdigit():
            ch_num = int(pattern_key)
            if ch_num in self.master_timings:
                pattern = self.master_timings[ch_num]
                print(f"▶ Playing master timing {ch_num} on channel {channel}")
                self._execute_pattern(pattern, channel, loops)
                return

        # Try patterns.json
        if pattern_key in self.patterns:
            pattern = self.patterns[pattern_key]
            print(f"▶ Playing '{pattern_key}' on channel {channel}")
            self._execute_pattern(pattern, channel, loops)
        else:
            print(f"✗ Pattern '{pattern_key}' not found")
            print(f"Available patterns: {list(self.patterns.keys())}")
            print(f"Master timings: {list(self.master_timings.keys())}")

    def _execute_pattern(self, pattern: List, channel: int, loops: int):
        """Execute pattern timing with nanosecond precision"""
        for loop in range(loops):
            if loops > 1:
                print(f"  Loop {loop + 1}/{loops}")

            for state, duration in pattern:
                value = 255 if state == "ON" else 0

                # Set channel and sleep with precise timing
                start = time.perf_counter()
                self.dmx.set_channel(channel, value)

                # Busy-wait for precise timing (sleep is not accurate enough)
                while (time.perf_counter() - start) < duration:
                    pass

        # Ensure channel is OFF at the end
        self.dmx.set_channel(channel, 0)
        print("✓ Pattern complete")


def main():
    if len(sys.argv) < 3:
        print("═" * 60)
        print("DIRECT DMX CONTROLLER - Precise Timing Control")
        print("═" * 60)
        print("\nUsage:")
        print("  python direct_dmx_controller.py <pattern> <channel> [loops]")
        print("\nExamples:")
        print("  python direct_dmx_controller.py A 1        # Play 'A' on channel 1")
        print(
            "  python direct_dmx_controller.py 1 7        # Play master timing #1 on channel 7"
        )
        print(
            "  python direct_dmx_controller.py SOS 3 5    # Play 'SOS' 5 times on channel 3"
        )
        print("\nAvailable in patterns.json:")
        try:
            with open(PATTERNS_FILE) as f:
                patterns = json.load(f)
            print(f"  {', '.join(patterns.keys())}")
        except:
            print("  (patterns.json not found)")
        print("\nMaster timings (channels 1-12 from timings file)")
        print("═" * 60)
        return

    pattern = sys.argv[1]
    channel = int(sys.argv[2])
    loops = int(sys.argv[3]) if len(sys.argv) > 3 else 1

    # Initialize
    dmx = DMXController()
    dmx.connect()

    player = PatternPlayer(dmx)

    try:
        player.play_pattern(pattern, channel, loops)
    except KeyboardInterrupt:
        print("\n⏸ Interrupted by user")
    finally:
        dmx.close()


if __name__ == "__main__":
    main()
