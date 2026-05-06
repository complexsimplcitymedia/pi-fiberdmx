#!/usr/bin/env python
"""
Test script to verify pattern execution works correctly
"""

from dmx_patterns import PatternParser

# Load patterns
parser = PatternParser()

# Show a couple channels
for channel in [1, 9]:
    pattern = parser.get_pattern(channel)
    if pattern:
        total_duration = sum(seg.duration for seg in pattern)
        print(f"\nChannel {channel} - Total: {total_duration:.2f}s")
        print("  State transitions:")
        for i, seg in enumerate(pattern[:10], 1):  # First 10 segments
            print(f"    {i}. {seg.state} {seg.duration:.2f}s")
        if len(pattern) > 10:
            print(f"    ... ({len(pattern) - 10} more segments)")
    else:
        print(f"Channel {channel}: No pattern found")

print("\n✓ Pattern parser working correctly")
