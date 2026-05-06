#!/usr/bin/env python3
"""
LIVE DMX CONTROL - Get the lights flashing NOW!
This script connects to the DMX adapter and gives you immediate control
"""

import os
import time
import serial
import serial.tools.list_ports

def find_dmx_adapter():
    """Find the FTDI DMX adapter"""
    print("🔍 Searching for DMX adapter...")
    ports = list(serial.tools.list_ports.comports())

    for port in ports:
        print(f"  Found: {port.device} - {port.description}")
        # Look for FTDI devices
        if 'FTDI' in port.description or 'USB' in port.description or 'Serial' in port.description:
            print(f"  ✅ DMX adapter found: {port.device}")
            return port.device

    # Try common paths
    common_paths = ['/dev/ttyUSB0', '/dev/ttyUSB1', '/dev/ttyACM0', 'COM3', 'COM4', 'COM5']
    for path in common_paths:
        if os.path.exists(path):
            print(f"  ✅ Found potential DMX device: {path}")
            return path

    return None

def send_dmx_frame(ser, channels):
    """
    Send a DMX frame
    channels: list of 512 values (0-255)
    """
    if not ser:
        return False

    try:
        # DMX Break (88-176 microseconds)
        ser.break_condition = True
        time.sleep(0.0001)  # 100 microseconds

        # Mark After Break (8-16 microseconds)
        ser.break_condition = False
        time.sleep(0.000012)  # 12 microseconds

        # Send start code (0x00) + 512 channel values
        frame = bytes([0] + channels[:512])
        ser.write(frame)

        return True
    except Exception as e:
        print(f"❌ Error sending DMX frame: {e}")
        return False

def flash_channel(ser, channel, count=5, duration=0.5):
    """Flash a specific channel on/off"""
    print(f"⚡ Flashing channel {channel}...")

    channels = [0] * 512

    for i in range(count):
        # ON
        channels[channel - 1] = 255
        send_dmx_frame(ser, channels)
        print(f"  🔆 Channel {channel} ON")
        time.sleep(duration)

        # OFF
        channels[channel - 1] = 0
        send_dmx_frame(ser, channels)
        print(f"  🔅 Channel {channel} OFF")
        time.sleep(duration)

def all_on(ser, channels_list):
    """Turn on multiple channels"""
    print(f"🔆 Turning ON channels: {channels_list}")
    channels = [0] * 512

    for ch in channels_list:
        channels[ch - 1] = 255

    send_dmx_frame(ser, channels)
    print("  ✅ Channels ON")

def all_off(ser):
    """Turn off all channels"""
    print("🔅 All channels OFF")
    channels = [0] * 512
    send_dmx_frame(ser, channels)
    print("  ✅ All OFF")

def main():
    print("="*60)
    print("🚀 LIVE DMX CONTROL - LET'S MAKE THESE LIGHTS FLASH!")
    print("="*60)

    # Find DMX adapter
    dmx_port = find_dmx_adapter()

    if not dmx_port:
        print("\n❌ No DMX adapter found!")
        print("\nTroubleshooting:")
        print("  1. Check USB connection")
        print("  2. Check if driver is loaded: lsusb")
        print("  3. Check permissions: sudo chmod 666 /dev/ttyUSB*")
        return

    print(f"\n📡 Connecting to DMX adapter: {dmx_port}")

    try:
        # Open serial connection
        ser = serial.Serial(
            dmx_port,
            baudrate=250000,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_TWO,
            timeout=1
        )

        print("✅ DMX adapter connected!")
        print(f"   Port: {dmx_port}")
        print(f"   Baud: 250000")

        # Make sure everything is off first
        all_off(ser)
        time.sleep(0.5)

        print("\n" + "="*60)
        print("🎉 STARTING LIGHT SHOW!")
        print("="*60)

        # Test sequence
        print("\n1. Testing Channel 1...")
        flash_channel(ser, 1, count=3, duration=0.3)

        time.sleep(1)

        print("\n2. Testing Channel 2...")
        flash_channel(ser, 2, count=3, duration=0.3)

        time.sleep(1)

        print("\n3. All channels 1-6 ON...")
        all_on(ser, [1, 2, 3, 4, 5, 6])
        time.sleep(2)

        print("\n4. Sequential flash...")
        for ch in range(1, 7):
            print(f"   Channel {ch}")
            channels = [0] * 512
            channels[ch - 1] = 255
            send_dmx_frame(ser, channels)
            time.sleep(0.2)

        time.sleep(1)

        print("\n5. All OFF")
        all_off(ser)

        print("\n" + "="*60)
        print("✅ TEST COMPLETE!")
        print("="*60)
        print("\n🎯 Next steps:")
        print("  - Run pattern sequences with dmx_controller.py")
        print("  - Load Morse timing patterns")
        print("  - Control via web interface")

        ser.close()

    except serial.SerialException as e:
        print(f"\n❌ Serial port error: {e}")
        print("\nTry:")
        print(f"  sudo chmod 666 {dmx_port}")
        print("  sudo usermod -a -G dialout $USER")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

