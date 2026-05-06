#!/usr/bin/env bash
set -euo pipefail

# Kill the all-channels runner quickly so the serial is free
/usr/bin/pkill -f dmx_patterns.py || true

# Tell systemd to stop the all-channels service without waiting
/bin/systemctl stop --no-block fiber-dmx-all || true

# Small pause so the kernel releases the TTY
sleep 0.3

# Extra safety: flush DMX to black if ui worker left anything up (best-effort)
if [ -e /dev/ttyUSB0 ] || [ -e /dev/dmx-usb ]; then
  python3 - <<'PY'
import os, time, serial
port="/dev/dmx-usb" if os.path.exists("/dev/dmx-usb") else "/dev/ttyUSB0"
try:
    ser=serial.Serial(port, baudrate=250000, bytesize=8, parity='N', stopbits=2, timeout=0.2)
    payload=bytes([0]+[0]*512)
    ser.break_condition=True; time.sleep(0.0001)
    ser.break_condition=False; time.sleep(0.000012)
    ser.write(payload)
    ser.close()
except Exception:
    pass
PY
fi

# Make sure any outstanding writes hit disk
/sbin/sync
sleep 0.5

# Clean power-off (safer for filesystem than reboot)
/bin/systemctl poweroff
