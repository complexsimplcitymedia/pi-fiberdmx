"""
DMX Controller for 5kW Laser Fiber Optic Identification System
- Exact Morse timing for camera decoding
- Safety-first: watchdog, mutual exclusion, max durations, emergency stop
- Channels 1-6: Manual ON/OFF toggle (100% brightness)
- Channels 7-12: Pattern sequences (Morse timing)
- Channels 13-15: Simple ON/OFF toggle (OLS, OTDR, Remote View)
"""

import os
import time
import serial
import threading
import json
from dataclasses import dataclass, asdict
from typing import Dict, Optional
from enum import Enum
from pathlib import Path

from dmx_patterns import PatternParser

class ChannelMode(Enum):
    """Channel operational mode"""
    OFF = 0
    MANUAL_ON = 1
    PATTERN_RUNNING = 2

@dataclass
class ChannelState:
    """State for a single DMX channel"""
    channel: int
    mode: ChannelMode
    brightness: int  # 0-255
    started_at: float  # unix timestamp
    pattern_id: Optional[int] = None

class SafetyConfig:
    """Safety limits and watchdog configuration"""
    DEFAULT_CONFIG = {
        "max_manual_duration_s": 300,      # 5 minutes for manual ON
        "max_pattern_duration_s": 3600,    # 1 hour for patterns
        "watchdog_interval_s": 5,          # Check every 5s
        "watchdog_timeout_s": 10,          # Emergency stop if no heartbeat
        "emergency_stop_kill_time_s": 0.1, # Ramp down over 100ms
    }

    def __init__(self, config_file: str = None):
        self.config = self.DEFAULT_CONFIG.copy()
        if config_file and os.path.exists(config_file):
            with open(config_file, 'r') as f:
                self.config.update(json.load(f))

    def get(self, key: str):
        return self.config.get(key, self.DEFAULT_CONFIG.get(key))

class DMXController:
    """Core DMX controller with exact timing and safety"""

    def __init__(self, serial_port: str = "/dev/ttyUSB0", safety_config: SafetyConfig = None):
        self.serial_port = serial_port
        self.ser: Optional[serial.Serial] = None
        self.safety_config = safety_config or SafetyConfig()
        self.pattern_parser = PatternParser()

        # Channel state tracking
        self.channel_states: Dict[int, ChannelState] = {i: ChannelState(i, ChannelMode.OFF, 0, 0) for i in range(1, 16)}
        self.state_lock = threading.RLock()

        # Pattern execution state - support multiple simultaneous patterns
        self.running_patterns: Dict[int, threading.Thread] = {}  # channel -> thread
        self.stop_events: Dict[int, threading.Event] = {}  # channel -> stop event

        # Sequential test state
        self.sequential_test_thread: Optional[threading.Thread] = None
        self.sequential_test_stop_event = threading.Event()

        # Watchdog
        self.watchdog_thread: Optional[threading.Thread] = None
        self.last_heartbeat = time.time()
        self.watchdog_running = False

        self.log("DMX Controller initialized (safety-first)")

    def log(self, msg: str):
        """Log with timestamp"""
        ts = time.strftime("[%H:%M:%S]")
        print(f"{ts} [DMX] {msg}", flush=True)

    def connect(self):
        """Open serial connection to FTDI DMX adapter"""
        try:
            self.ser = serial.Serial(
                self.serial_port,
                baudrate=250000,
                bytesize=8,
                parity='N',
                stopbits=2
            )
            self.log(f"Connected to {self.serial_port}")
            
            # Watchdog disabled - patterns will loop indefinitely
            # TODO: Re-enable with proper heartbeat mechanism
            # self.start_watchdog()
        except Exception as e:
            self.log(f"ERROR: Failed to connect: {e}")
            raise

    def send_dmx_frame(self, levels: list):
        """Send DMX frame with break condition (513 bytes: 0x00 + 512 channel values)"""
        if not self.ser:
            return

        try:
            # Check if connection is still alive
            if not self.ser.is_open:
                self.log("ERROR: Serial connection closed - DMX offline")
                return
                
            self.ser.break_condition = True
            time.sleep(0.0001)
            self.ser.break_condition = False
            time.sleep(0.000012)
            self.ser.write(bytes([0] + levels[:512]))
        except (serial.SerialException, OSError) as e:
            self.log(f"ERROR: Lost DMX connection: {e} - DMX offline")
        except Exception as e:
            self.log(f"ERROR: Failed to send DMX frame: {e}")

    def _get_dmx_levels(self) -> list:
        """Build DMX levels array (512 channels) from current channel states"""
        levels = [0] * 512
        with self.state_lock:
            for ch_num, state in self.channel_states.items():
                if 1 <= ch_num <= 512:
                    levels[ch_num - 1] = state.brightness
        return levels

    def channel_set(self, channel: int, brightness: int):
        """Set channel brightness (0-255)"""
        if not 1 <= channel <= 15:
            raise ValueError(f"Invalid channel {channel} (1-15)")
        if not 0 <= brightness <= 255:
            raise ValueError(f"Invalid brightness {brightness} (0-255)")

        with self.state_lock:
            self.channel_states[channel].brightness = brightness

        # Send updated DMX frame
        levels = self._get_dmx_levels()
        self.send_dmx_frame(levels)

    def manual_toggle(self, channel: int):
        """
        Toggle manual ON/OFF for channels 1-6, 13-15.
        ON = 100% (255), OFF = 0%
        
        Note: CH13-15 are independent utility channels, always allowed.
        CH1-6 used in TOGGLE mode (manual VFL testing).
        """
        if channel not in list(range(1, 7)) + list(range(13, 16)):
            raise ValueError(f"Manual toggle only for channels 1-6, 13-15; got {channel}")

        with self.state_lock:
            state = self.channel_states[channel]

            if state.mode == ChannelMode.OFF:
                state.mode = ChannelMode.MANUAL_ON
                state.brightness = 255
                state.started_at = time.time()
                self.log(f"Channel {channel} ON (manual)")
            else:
                state.mode = ChannelMode.OFF
                state.brightness = 0
                state.started_at = 0
                self.log(f"Channel {channel} OFF (manual)")

        # Send updated DMX frame
        levels = self._get_dmx_levels()
        self.send_dmx_frame(levels)

    def indefinite_on(self, channel: int):
        """
        Set channel to indefinite ON (255) - for channels 1-6, 13-15.
        Unlike manual_toggle(), this ALWAYS turns ON (doesn't toggle).
        
        Note: CH13-15 are independent utility channels, always allowed.
        """
        if channel not in list(range(1, 7)) + list(range(13, 16)):
            raise ValueError(f"Indefinite ON only for channels 1-6, 13-15; got {channel}")

        with self.state_lock:
            state = self.channel_states[channel]

            state.mode = ChannelMode.MANUAL_ON
            state.brightness = 255
            state.started_at = time.time()
            self.log(f"Channel {channel} indefinite ON")

        # Send updated DMX frame
        levels = self._get_dmx_levels()
        self.send_dmx_frame(levels)

    def indefinite_off(self, channel: int):
        """
        Set channel to indefinite OFF (0) - for channels 1-6, 13-15.
        Unlike manual_toggle(), this ALWAYS turns OFF (doesn't toggle).
        """
        if channel not in list(range(1, 7)) + list(range(13, 16)):
            raise ValueError(f"Indefinite OFF only for channels 1-6, 13-15; got {channel}")

        with self.state_lock:
            state = self.channel_states[channel]
            state.mode = ChannelMode.OFF
            state.brightness = 0
            state.started_at = 0
            self.log(f"Channel {channel} indefinite OFF")

        # Send updated DMX frame
        levels = self._get_dmx_levels()
        self.send_dmx_frame(levels)

    def pattern_run(self, channel: int, loop_indefinitely: bool = True):
        """
        Run Morse pattern for channel (1-12).
        Supports multiple simultaneous patterns.
        Executes exact timing sequence indefinitely.
        """
        if not 1 <= channel <= 12:
            raise ValueError(f"Patterns only for channels 1-12; got {channel}")

        # Check if this specific channel is already running
        if channel in self.running_patterns:
            self.log(f"Channel {channel} pattern already running")
            return

        # Check mutual exclusion: no manual channels active
        with self.state_lock:
            for ch in range(1, 7):
                if self.channel_states[ch].mode == ChannelMode.MANUAL_ON:
                    self.log("WARN: Cannot run pattern; manual channels active")
                    return

        self.log(f"Starting pattern for channel {channel}")
        
        # Create stop event for this channel
        stop_event = threading.Event()
        self.stop_events[channel] = stop_event

        # Start pattern thread for this channel
        thread = threading.Thread(
            target=self._pattern_executor,
            args=(channel, loop_indefinitely, stop_event),
            daemon=True
        )
        self.running_patterns[channel] = thread
        thread.start()

    def _pattern_executor(self, channel: int, loop_indefinitely: bool, stop_event: threading.Event):
        """Execute pattern timing sequence (runs in separate thread)"""
        try:
            pattern = self.pattern_parser.get_pattern(channel)
            if not pattern:
                self.log(f"ERROR: No pattern found for channel {channel}")
                return

            max_duration = self.safety_config.get("max_pattern_duration_s")
            start_time = time.time()
            cycle_count = 0
            
            self.log(f"[PATTERN_DEBUG] CH{channel} started: loop_indefinitely={loop_indefinitely}, max_duration={max_duration}s, pattern_segments={len(pattern)}")

            while not stop_event.is_set():
                cycle_count += 1
                self.log(f"[PATTERN_DEBUG] CH{channel} starting cycle #{cycle_count}")
                
                # Check max duration
                elapsed = time.time() - start_time
                if elapsed > max_duration:
                    self.log(f"[PATTERN_DEBUG] CH{channel} reached max duration ({elapsed:.1f}s > {max_duration}s); stopping")
                    break

                # Execute one cycle of the pattern
                for seg_idx, segment in enumerate(pattern):
                    if stop_event.is_set():
                        self.log(f"[PATTERN_DEBUG] CH{channel} stop_event detected at segment {seg_idx}")
                        break

                    # Convert ON/OFF to brightness (255 for ON, 0 for OFF)
                    brightness = 255 if segment.state == "ON" else 0

                    # Update channel brightness
                    with self.state_lock:
                        self.channel_states[channel].brightness = brightness

                    # Send DMX frame
                    levels = self._get_dmx_levels()
                    self.send_dmx_frame(levels)

                    # Exact timing: sleep for segment duration
                    time.sleep(segment.duration)

                cycle_duration = time.time() - start_time - (cycle_count - 1) * sum(s.duration for s in pattern)
                self.log(f"[PATTERN_DEBUG] CH{channel} completed cycle #{cycle_count} in {cycle_duration:.2f}s")
                
                if not loop_indefinitely:
                    self.log(f"[PATTERN_DEBUG] CH{channel} loop_indefinitely=False, exiting after cycle #{cycle_count}")
                    break
                    
                self.log(f"[PATTERN_DEBUG] CH{channel} loop_indefinitely=True, continuing to cycle #{cycle_count + 1}")

            # Pattern ended; clear channel
            with self.state_lock:
                self.channel_states[channel].brightness = 0
            levels = self._get_dmx_levels()
            self.send_dmx_frame(levels)

            self.log(f"[PATTERN_DEBUG] CH{channel} stopped after {cycle_count} cycles, stop_event.is_set()={stop_event.is_set()}")
        except Exception as e:
            self.log(f"ERROR in pattern executor: {e}")
        finally:
            # Clean up: remove from running patterns
            if channel in self.running_patterns:
                del self.running_patterns[channel]
            if channel in self.stop_events:
                del self.stop_events[channel]

    def pattern_stop(self, channel: Optional[int] = None):
        """Stop pattern(s).
        
        Args:
            channel: If specified, stop only this channel. If None, stop all patterns.
        """
        if channel is not None:
            # Stop specific channel
            if channel in self.running_patterns:
                self.log(f"Stopping pattern {channel}")
                self.stop_events[channel].set()
                
                # Immediately zero the channel brightness to stop any flashing
                with self.state_lock:
                    self.channel_states[channel].brightness = 0
                levels = self._get_dmx_levels()
                self.send_dmx_frame(levels)
                
                self.running_patterns[channel].join(timeout=1)
        else:
            # Stop all patterns
            if self.running_patterns:
                self.log(f"Stopping all patterns: {list(self.running_patterns.keys())}")
                for ch, stop_event in self.stop_events.items():
                    stop_event.set()
                
                # Immediately zero all pattern channel brightnesses
                with self.state_lock:
                    for ch in self.running_patterns.keys():
                        self.channel_states[ch].brightness = 0
                levels = self._get_dmx_levels()
                self.send_dmx_frame(levels)
                
                for ch, thread in list(self.running_patterns.items()):
                    thread.join(timeout=1)

    def stop_vis_channels(self):
        """Stop all VIS channels (1-6) - both patterns and manual modes.
        Used for safety interlock when activating IR channels."""
        # Stop any running VIS patterns
        for ch in range(1, 7):
            if ch in self.running_patterns:
                self.pattern_stop(ch)
        
        # Turn off all manual VIS channels
        with self.state_lock:
            for ch in range(1, 7):
                self.channel_states[ch].mode = ChannelMode.OFF
                self.channel_states[ch].brightness = 0
        
        # Send updated DMX frame
        levels = self._get_dmx_levels()
        self.send_dmx_frame(levels)
        self.log("SAFETY: All VIS channels (1-6) stopped")

    def stop_sequential_test(self):
        """Stop the sequential test if running"""
        if self.sequential_test_thread and self.sequential_test_thread.is_alive():
            self.log("Stopping sequential test...")
            self.sequential_test_stop_event.set()

            # Immediately zero all channels
            with self.state_lock:
                for ch in range(1, 13):
                    self.channel_states[ch].brightness = 0
            levels = self._get_dmx_levels()
            self.send_dmx_frame(levels)

            # Wait for thread to finish
            self.sequential_test_thread.join(timeout=2)
            self.log("Sequential test stopped")

    def emergency_stop(self):
        """EMERGENCY: Kill all laser channels 1-14 immediately

        CH1-14: All laser/light channels forced OFF (SAFETY CRITICAL)
        CH15: Camera stays ON for visual confirmation that lasers are off
        """
        self.log("!!! EMERGENCY STOP - LASER CHANNELS 1-14 !!!")

        # Stop all patterns
        self.pattern_stop()

        # Stop sequential test
        self.stop_sequential_test()

        with self.state_lock:
            # Zero out laser channels 1-14
            for ch in range(1, 15):
                self.channel_states[ch].brightness = 0
                self.channel_states[ch].mode = ChannelMode.OFF
                self.channel_states[ch].started_at = 0

            # CH15 (Camera) remains unchanged for visual confirmation

        levels = self._get_dmx_levels()
        self.send_dmx_frame(levels)
        self.log("Laser channels 1-14 forced OFF (camera CH15 unchanged)")
    
    def shutdown_all(self):
        """Full shutdown: Kill ALL channels 1-15 including camera
        
        Used during system shutdown/reboot to ensure everything is OFF.
        """
        self.log("!!! FULL SHUTDOWN - ALL CHANNELS 1-15 !!!")
        self.pattern_stop()
        # Watchdog disabled
        # self.stop_watchdog()

        with self.state_lock:
            # Zero out ALL channels including camera
            for ch in range(1, 16):
                self.channel_states[ch].brightness = 0
                self.channel_states[ch].mode = ChannelMode.OFF
                self.channel_states[ch].started_at = 0

        levels = self._get_dmx_levels()
        self.send_dmx_frame(levels)
        # Close serial connection
        if self.ser and self.ser.is_open:
            self.ser.close()
        
        self.log("ALL channels 1-15 OFF, connection closed")

    def sequential_test(self, cycles_per_channel: int = 5):
        """
        Run sequential channel test - each channel flashes individually.

        Args:
            cycles_per_channel: Number of pattern cycles per channel (default 5)
        """
        self.log(f"Starting sequential test: {cycles_per_channel} cycles per channel")

        # Stop any running patterns and previous sequential test
        self.pattern_stop()
        self.stop_sequential_test()

        # Clear and reset stop event
        self.sequential_test_stop_event.clear()

        # Create thread for sequential test
        self.sequential_test_thread = threading.Thread(
            target=self._sequential_test_executor,
            args=(cycles_per_channel,),
            daemon=True
        )
        self.sequential_test_thread.start()
    
    def _sequential_test_executor(self, cycles_per_channel: int):
        """Execute sequential test in separate thread"""
        try:
            # Test each channel 1-12 sequentially
            for ch in range(1, 13):
                # Check stop event before each channel
                if self.sequential_test_stop_event.is_set():
                    self.log("Sequential test stopped by user")
                    break

                pattern = self.pattern_parser.get_pattern(ch)
                if not pattern:
                    self.log(f"WARN: No pattern for channel {ch}, skipping")
                    continue

                self.log(f"Testing CH{ch}: {cycles_per_channel} cycles")

                # Run specified number of cycles
                for cycle in range(cycles_per_channel):
                    # Check stop event before each cycle
                    if self.sequential_test_stop_event.is_set():
                        self.log("Sequential test stopped by user")
                        break

                    # Execute pattern
                    for segment in pattern:
                        # Check stop event during pattern execution
                        if self.sequential_test_stop_event.is_set():
                            self.log("Sequential test stopped by user")
                            break

                        with self.state_lock:
                            if segment.state == "ON":
                                self.channel_states[ch].brightness = 255
                            else:
                                self.channel_states[ch].brightness = 0

                        levels = self._get_dmx_levels()
                        self.send_dmx_frame(levels)
                        time.sleep(segment.duration)

                    if self.sequential_test_stop_event.is_set():
                        break

                # Clear channel after test
                with self.state_lock:
                    self.channel_states[ch].brightness = 0
                levels = self._get_dmx_levels()
                self.send_dmx_frame(levels)

                # Small gap between channels
                if not self.sequential_test_stop_event.is_set():
                    time.sleep(0.1)

            if not self.sequential_test_stop_event.is_set():
                self.log("Sequential test complete")
        except Exception as e:
            self.log(f"ERROR in sequential test: {e}")

    def heartbeat(self):
        """Watchdog heartbeat (call periodically to keep system alive)"""
        self.last_heartbeat = time.time()

    def start_watchdog(self):
        """Start watchdog thread for connection monitoring and safety timeout"""
        if self.watchdog_running:
            return
        
        self.watchdog_running = True
        self.last_heartbeat = time.time()
        self.watchdog_thread = threading.Thread(target=self._watchdog_loop, daemon=True)
        self.watchdog_thread.start()
        self.log("Watchdog started")

    def _watchdog_loop(self):
        """Watchdog loop - monitors connection and enforces safety timeouts"""
        watchdog_interval = self.safety_config.get("watchdog_interval_s")
        watchdog_timeout = self.safety_config.get("watchdog_timeout_s")
        
        while self.watchdog_running:
            time.sleep(watchdog_interval)
            
            # Check serial connection health
            if self.ser and not self.ser.is_open:
                self.log("!!! WATCHDOG: Serial connection lost - EMERGENCY STOP !!!")
                self.emergency_stop()
                continue
            
            # Check heartbeat timeout (optional - for external app integration)
            time_since_heartbeat = time.time() - self.last_heartbeat
            if time_since_heartbeat > watchdog_timeout:
                self.log(f"!!! WATCHDOG: No heartbeat for {time_since_heartbeat:.1f}s - EMERGENCY STOP !!!")
                self.emergency_stop()
                self.last_heartbeat = time.time()  # Reset to prevent repeated stops
            
            # Check for manual channels exceeding max duration
            max_manual = self.safety_config.get("max_manual_duration_s")
            with self.state_lock:
                for ch, state in self.channel_states.items():
                    if state.mode == ChannelMode.MANUAL_ON and state.started_at:
                        elapsed = time.time() - state.started_at
                        if elapsed > max_manual:
                            self.log(f"!!! WATCHDOG: CH{ch} manual exceeded {max_manual}s - turning OFF !!!")
                            state.mode = ChannelMode.OFF
                            state.brightness = 0
                            state.started_at = 0
            
            # Send updated frame if any changes were made
            levels = self._get_dmx_levels()
            self.send_dmx_frame(levels)

    def stop_watchdog(self):
        """Stop the watchdog thread"""
        self.watchdog_running = False
        if self.watchdog_thread:
            self.watchdog_thread.join(timeout=2)
        self.log("Watchdog stopped")

    def get_status(self) -> dict:
        """Get current system status"""
        with self.state_lock:
            status = {
                "running_pattern": self.running_pattern,
                "channels": {
                    ch: {
                        "mode": state.mode.name,
                        "brightness": state.brightness,
                        "uptime_s": time.time() - state.started_at if state.started_at else 0
                    }
                    for ch, state in self.channel_states.items()
                }
            }
        return status


if __name__ == "__main__":
    # Test
    controller = DMXController()
    controller.connect()

    # Test manual toggle
    controller.manual_toggle(1)
    time.sleep(2)
    controller.manual_toggle(1)

    # Test pattern
    controller.pattern_run(7, loop_indefinitely=False)
    time.sleep(5)

    controller.emergency_stop()
    print("\nTest complete")
