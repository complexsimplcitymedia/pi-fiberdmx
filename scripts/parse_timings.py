#!/usr/bin/env python
"""
Parse Laser_Master_patterns_timings.txt and generate correct ON/OFF patterns for all 12 channels
"""

def parse_timings():
    """Extract A-D-# patterns from master timings file"""
    with open('/home/laser-dmx/fiber-laser-dmx/data/Laser_Master_patterns_timings.txt', 'r') as f:
        lines = f.readlines()
    
    patterns = {}
    
    # First line format: "1. A .12s,.12s,.36s,.84s - D .36s,.12s,.12s,.12s,.12s,.84s - 1 .12s,.12s,.36s,.12s,.36s,.12s,.36s,.12s,.36s,.99s"
    for line in lines:
        if not line.strip() or line.startswith(' '):
            continue
        
        parts = line.split(' - ')
        if len(parts) < 3:
            continue
        
        # Extract channel number from first part
        first_part = parts[0].strip()
        if not first_part[0].isdigit():
            continue
        
        channel = int(first_part.split('.')[0])
        
        # Parse A, D, and digit sections
        pattern = []
        
        for section in parts:
            # Extract timing values
            if '.' in section:
                # Get the timing string after the letter (A, D, U, or digit)
                timing_str = section.split()[-1]  # Get last part with timings
                times = []
                for val in timing_str.split(','):
                    val = val.strip().rstrip('s')
                    try:
                        times.append(float(val))
                    except:
                        pass
                
                # Alternate ON/OFF starting with ON
                for i, t in enumerate(times):
                    value = 255 if i % 2 == 0 else 0
                    pattern.append((value, t))
        
        if pattern:
            patterns[channel] = pattern
    
    return patterns

if __name__ == "__main__":
    patterns = parse_timings()
    for ch, pattern in sorted(patterns.items()):
        print(f"Channel {ch}:")
        for i, (val, dur) in enumerate(pattern):
            state = "ON" if val == 255 else "OFF"
            print(f"  {i+1}. {state} {dur}s")
        print()
