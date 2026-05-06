#!/usr/bin/env python
"""
Pattern Flash Test Script - SEQUENTIAL ONLY
Each channel flashes individually - NO overlapping
5 cycles per channel, loops infinitely
"""

import os
import sys
import time
import serial
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from dmx_patterns import PatternParser

def find_port():
    """Find FTDI DMX adapter"""
    candidates = ["/dev/ttyUSB0", "/dev/ttyUSB1", "/dev/ttyACM0"]
    for port in candidates:
        if os.path.exists(port):
            return port
    raise RuntimeError("No DMX adapter found")

def send_dmx_frame(ser, levels):
    """Send DMX frame with break condition"""
    try:
        ser.break_condition = True
        time.sleep(0.0001)
        ser.break_condition = False
        time.sleep(0.000012)
        ser.write(bytes([0] + levels[:512]))
    except Exception as e:
        print(f"ERROR: {e}")

def clear_all(ser):
    """Explicitly clear ALL channels"""
    levels = [0] * 512
    send_dmx_frame(ser, levels)

def test_sequential():
    """Test each channel ONE AT A TIME - completely sequential"""
    print("=" * 70)
    print("SEQUENTIAL PATTERN TEST")
    print("Each channel flashes ALONE (no overlapping)")
    print("5 cycles per channel, infinite loop")
    print("=" * 70)
    print()
    
    # Connect
    try:
        port = find_port()
        ser = serial.Serial(port, baudrate=250000, bytesize=8, parity='N', stopbits=2)
        print(f"✓ Connected to {port}\n")
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return
    
    # Load patterns
    parser = PatternParser()
    if not parser.patterns:
        print("✗ No patterns loaded")
        ser.close()
        return
    
    # Infinite loop
    loop_num = 0
    try:
        while True:
            loop_num += 1
            print(f"\n{'='*70}")
            print(f"LOOP {loop_num}")
            print(f"{'='*70}\n")
            
            # Each channel sequentially
            for ch in range(1, 13):
                pattern = parser.get_pattern(ch)
                if not pattern:
                    continue
                
                cycle_time = sum(seg.duration for seg in pattern)
                print(f"CH {ch:2d}: Starting (5 × {cycle_time:.2f}s)")
                
                # 5 cycles
                for cycle in range(1, 6):
                    start = time.time()
                    
                    # Play pattern
                    for segment in pattern:
                        # Create frame with ONLY this channel
                        levels = [0] * 512
                        if segment.state == "ON":
                            levels[ch - 1] = 255
                        else:
                            levels[ch - 1] = 0
                        
                        send_dmx_frame(ser, levels)
                        time.sleep(segment.duration)
                    
                    elapsed = time.time() - start
                    print(f"        Cycle {cycle}/5 ✓ ({elapsed:.2f}s)")
                
                # HARD CLEAR after each channel
                clear_all(ser)
                time.sleep(0.1)  # Gap between channels
                print()
            
            print(f"Loop {loop_num} complete.\n")
    
    except KeyboardInterrupt:
        print("\n✗ STOPPED")
        clear_all(ser)
    finally:
        clear_all(ser)
        ser.close()
        print("\n" + "=" * 70)
        print("All channels cleared")
        print("=" * 70)

if __name__ == "__main__":
    try:
        test_sequential()
    except KeyboardInterrupt:
        print("\n✗ Aborted")
        sys.exit(1)


