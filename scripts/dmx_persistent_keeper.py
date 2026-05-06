#!/usr/bin/env python3
"""
Persistent DMX Port Keeper - Never Release the Bind
Maintains constant DMX transmission to prevent other services from grabbing /dev/ttyUSB0
Based on dmx_cycle_reboot.py pattern but optimized for low power draw

Safety Features:
- 30 FPS keepalive (not 44) to avoid power issues with Pi 5 + custom screen
- Continuous transmission even when idle (sends zeros)
- Port health monitoring
- Emergency shutdown capability
- Must run as root for port binding priority

Usage:
    sudo python3 dmx_persistent_keeper.py
"""

import os
import sys
import time
import serial
import signal
import threading

# Add scripts directory to path
sys.path.insert(0, '/home/laser-dmx/fiber-laser-dmx/scripts')

class PersistentDMXKeeper:
    """Maintains persistent DMX connection with continuous transmission"""

    def __init__(self, port="/dev/ttyUSB0", fps=30):
        self.port = port
        self.fps = fps
        self.frame_delay = 1.0 / fps
        self.ser = None
        self.running = False
        self.keepalive_thread = None
        self.last_frame_time = 0
        self.frame_count = 0

        # DMX levels (512 channels)
        self.levels = [0] * 512
        self.levels_lock = threading.RLock()

    def log(self, msg):
        """Log with timestamp"""
        print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

    def require_root(self):
        """Verify running as root"""
        if os.geteuid() != 0:
            self.log("ERROR: This script must be run as root (sudo)")
            sys.exit(1)

    def connect(self):
        """Open serial connection - NEVER CLOSE IT"""
        try:
            self.ser = serial.Serial(
                self.port,
                baudrate=250000,
                bytesize=8,
                parity='N',
                stopbits=2,
                timeout=0.1
            )
            self.log(f"✓ Connected to {self.port} (baudrate=250000, 8N2)")
            self.log(f"✓ Keepalive transmission at {self.fps} FPS")
            return True
        except Exception as e:
            self.log(f"✗ Failed to connect: {e}")
            return False

    def send_dmx_frame(self, levels):
        """Send DMX frame with proper break condition"""
        if not self.ser:
            return False

        try:
            # DMX break condition (100μs)
            self.ser.break_condition = True
            time.sleep(0.0001)
            self.ser.break_condition = False

            # Mark After Break (12μs)
            time.sleep(0.000012)

            # Send start code (0x00) + 512 channel values
            self.ser.write(bytes([0] + levels[:512]))

            self.frame_count += 1
            return True
        except Exception as e:
            self.log(f"✗ Frame send error: {e}")
            return False

    def keepalive_loop(self):
        """Continuous transmission loop - NEVER STOPS"""
        self.log("Starting continuous DMX transmission (keepalive mode)")

        while self.running:
            start = time.time()

            # Get current levels (thread-safe)
            with self.levels_lock:
                current_levels = self.levels.copy()

            # Send DMX frame
            if self.send_dmx_frame(current_levels):
                self.last_frame_time = time.time()

            # Log every 1000 frames
            if self.frame_count % 1000 == 0:
                self.log(f"Keepalive: {self.frame_count} frames sent, port binding maintained")

            # Sleep to maintain target FPS
            elapsed = time.time() - start
            sleep_time = max(0, self.frame_delay - elapsed)
            time.sleep(sleep_time)

        self.log("Keepalive loop stopped")

    def set_channel(self, channel, brightness):
        """Set channel brightness (1-512, 0-255)"""
        if not 1 <= channel <= 512:
            return False
        if not 0 <= brightness <= 255:
            return False

        with self.levels_lock:
            self.levels[channel - 1] = brightness
        return True

    def emergency_stop(self):
        """Kill all channels immediately"""
        self.log("!!! EMERGENCY STOP - All channels OFF !!!")
        with self.levels_lock:
            self.levels = [0] * 512
        time.sleep(0.1)  # Let one frame go through

    def start(self):
        """Start persistent keeper"""
        self.require_root()

        if not self.connect():
            return False

        self.running = True

        # Start keepalive thread
        self.keepalive_thread = threading.Thread(
            target=self.keepalive_loop,
            daemon=True
        )
        self.keepalive_thread.start()

        self.log("✓ Persistent DMX keeper started")
        self.log("✓ Port binding will be maintained until script exits")
        return True

    def stop(self):
        """Stop keeper (graceful shutdown)"""
        self.log("Stopping persistent keeper...")
        self.running = False

        if self.keepalive_thread:
            self.keepalive_thread.join(timeout=2)

        # Send final all-zero frame
        self.emergency_stop()

        if self.ser:
            self.ser.close()
            self.log("✓ Serial port closed")

    def health_check(self):
        """Check if DMX transmission is healthy"""
        if not self.running:
            return False

        # Check if frames are being sent (should be within last second)
        time_since_frame = time.time() - self.last_frame_time
        if time_since_frame > 1.0:
            self.log(f"⚠ WARNING: No frames sent for {time_since_frame:.2f}s")
            return False

        # Check if serial port still open
        if not self.ser or not self.ser.is_open:
            self.log("✗ CRITICAL: Serial port lost!")
            return False

        return True


def signal_handler(signum, frame):
    """Handle Ctrl+C and system signals"""
    print("\n[SIGNAL] Shutdown requested")
    if 'keeper' in globals():
        keeper.stop()
    sys.exit(0)


def main():
    """Main entry point"""
    global keeper

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("═" * 60)
    print("  PERSISTENT DMX PORT KEEPER")
    print("  Maintains /dev/ttyUSB0 binding with continuous transmission")
    print("═" * 60)

    keeper = PersistentDMXKeeper(port="/dev/ttyUSB0", fps=30)

    if not keeper.start():
        print("Failed to start keeper")
        sys.exit(1)

    # Main loop - monitor health and accept commands
    try:
        while True:
            time.sleep(10)

            # Health check
            if not keeper.health_check():
                print("[HEALTH] DMX transmission unhealthy!")
                # Don't exit - keep trying to transmit

    except KeyboardInterrupt:
        print("\n[CTRL+C] Shutting down...")
    finally:
        keeper.stop()
        print("Persistent keeper stopped")


if __name__ == "__main__":
    main()
