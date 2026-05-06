#!/usr/bin/env python
"""
Parse and manage laser Morse code patterns from Laser_Master_patterns_timings.txt
Exact timing sequences: A (fiber) + strand (D/G/U) + digit (1-12)
Patterns MUST start with ON, not OFF.
"""

import re
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class TimingSegment:
    """Single ON or OFF timing segment"""
    state: str  # "ON" or "OFF"
    duration: float  # seconds

class ChannelMode:
    PATTERN = "pattern"
    FULL_ON = "full_on"
    FULL_OFF = "full_off"

class PatternParser:
    def __init__(self, timings_file: str = "/home/laser-dmx/fiber-laser-dmx/data/Laser_Master_patterns_timings.txt"):
        self.timings_file = timings_file
        self.patterns: Dict[int, List[TimingSegment]] = {}  # channel -> pattern
        self.load_patterns()
    
    def load_patterns(self):
        """Parse master timings file and build complete A+strand+digit sequences"""
        with open(self.timings_file, 'r') as f:
            for line in f:
                line_stripped = line.strip()
                # Skip empty lines and header rows
                if not line_stripped or not line_stripped[0].isdigit():
                    continue
                
                # Parse line: " 1. A .12s,.12s,.36s,.84s - D .36s,.12s,.12s,.12s,.12s,.84s - 1 .12s,.12s,.36s,.12s,.36s,.12s,.36s,.12s,.36s,.99s"
                # Format: channel. A timing - strand timing - digit timing
                match = re.match(
                    r'\s*(\d+)\.\s+A\s+([\d.s,]+)\s+-\s+([A-Z])\s+([\d.s,]+)\s*-\s*(\d+)\s+([\d.s,]+)',
                    line_stripped
                )
                if not match:
                    continue
                
                channel = int(match.group(1))
                a_timing = match.group(2)          # A (fiber) timing
                # strand = match.group(3)  # D, G, or U (unused)
                strand_timing = match.group(4)      # Strand timing
                # digit = match.group(5)  # 1-12 (unused)
                digit_timing = match.group(6)       # Digit timing
                
                # Build complete sequence: A + strand + digit (NO gaps between)
                # The gaps are already embedded at the END of each section (.84s at end of A and strand)
                full_sequence = f"{a_timing},{strand_timing},{digit_timing}"
                pattern = self._parse_timing_string(full_sequence)
                
                self.patterns[channel] = pattern
    
    def _parse_timing_string(self, timing_str: str) -> List[TimingSegment]:
        """
        Parse timing string like ".12s,.12s,.36s,.84s" into segments.
        Timings alternate ON/OFF starting with ON.
        
        Example: ".12s,.12s,.36s,.84s" becomes:
        - 0.12s ON (dot)
        - 0.12s OFF (dot gap)
        - 0.36s ON (dash)
        - 0.84s OFF (letter gap)
        """
        # Extract all timing values (match .12s, .36s, .84s, .99s, etc.)
        values = re.findall(r'\.(\d+)s', timing_str)
        timings = [float(f"0.{v}") for v in values]
        
        segments = []
        for i, duration in enumerate(timings):
            # Even indices (0, 2, 4, ...) = ON, odd indices (1, 3, 5, ...) = OFF
            # This ensures pattern starts with ON (laser fires first)
            state = "ON" if i % 2 == 0 else "OFF"
            segments.append(TimingSegment(state, duration))
        
        return segments
    
    def get_pattern(self, channel: int) -> List[TimingSegment]:
        """Get pattern for a specific channel"""
        return self.patterns.get(channel, [])
    
    def display_patterns(self):
        """Print all patterns for verification"""
        for channel in sorted(self.patterns.keys()):
            pattern = self.patterns[channel]
            total_duration = sum(seg.duration for seg in pattern)
            print(f"\nChannel {channel}:")
            print(f"  Total cycle: {total_duration:.2f}s")
            for i, seg in enumerate(pattern, 1):
                print(f"    {i}. {seg.state} {seg.duration:.2f}s")

if __name__ == "__main__":
    parser = PatternParser()
    # Debug: show what was parsed
    if parser.patterns:
        parser.display_patterns()
    else:
        print("ERROR: No patterns parsed from file!")
        print("\nDebug: Reading first 5 lines of file:")
        with open(parser.timings_file, 'r') as f:
            for i, line in enumerate(f):
                if i < 5:
                    print(f"Line {i}: {repr(line)}")
                else:
                    break
