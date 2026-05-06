#!/usr/bin/env python
"""dmx_rebind.py — minimal USB driver rebind utility for FTDI/DMX adapters.

This script performs a soft unbind/bind of a USB device identified by VID/PID
and optional serial string. It is intentionally small and requires root.
"""

import os
import sys
import time
import argparse
import glob
import subprocess


def log(msg):
    print(time.strftime("[%H:%M:%S]"), msg, flush=True)


def require_root():
    if os.geteuid() != 0:
        log("This script must be run as root (sudo).")
        sys.exit(1)


def find_device(vid, pid, serial_hint=""):
    """Return the sysfs device id (basename) matching vid/pid and optional serial."""
    for d in glob.glob("/sys/bus/usb/devices/*"):
        vidf = os.path.join(d, "idVendor")
        pidf = os.path.join(d, "idProduct")
        if os.path.exists(vidf) and os.path.exists(pidf):
            try:
                v = open(vidf).read().strip()
                p = open(pidf).read().strip()
                if v.lower() == vid.lower() and p.lower() == pid.lower():
                    if serial_hint:
                        sf = os.path.join(d, "serial")
                        if os.path.exists(sf):
                            s = open(sf).read().strip()
                            if s != serial_hint:
                                continue
                        else:
                            continue
                    return os.path.basename(d)
            except Exception:
                continue
    return None


def driver_rebind(vid="0403", pid="6001", serial_hint="", timeout=5.0, dry_run=False):
    """Attempt a soft unbind/bind of the USB device identified by vid/pid.

    Returns True on success, False on failure.
    """
    log("Driver rebind: begin")
    # Ensure modules are loaded (best effort)
    subprocess.run(["modprobe", "usbserial"], check=False)
    subprocess.run(["modprobe", "ftdi_sio"], check=False)

    # Optional: write new_id to help ftdi_sio claim device
    new_id = "/sys/bus/usb-serial/drivers/ftdi_sio/new_id"
    try:
        if os.path.exists(new_id) and os.access(new_id, os.W_OK):
            if not dry_run:
                with open(new_id, "w") as f:
                    f.write(f"{vid} {pid}\n")
                log("Wrote new_id to ftdi_sio")
            else:
                log("(dry-run) would write new_id to ftdi_sio")
    except Exception as e:
        log(f"new_id write failed: {e}")

    # Trigger udev to ensure sysfs nodes are present
    subprocess.run(["udevadm", "trigger", "-s", "tty"], check=False)
    time.sleep(0.4)

    # Find matching device
    t0 = time.time()
    devpath = None
    while time.time() - t0 < float(timeout):
        devpath = find_device(vid, pid, serial_hint)
        if devpath:
            break
        time.sleep(0.2)

    if not devpath:
        log("Driver rebind: device path not found")
        return False

    unbind = "/sys/bus/usb/drivers/usb/unbind"
    bind = "/sys/bus/usb/drivers/usb/bind"
    try:
        if os.path.exists(unbind) and os.access(unbind, os.W_OK):
            if not dry_run:
                with open(unbind, "w") as f:
                    f.write(devpath)
                log(f"Wrote to unbind: {devpath}")
            else:
                log(f"(dry-run) would write to unbind: {devpath}")
        else:
            log("Cannot write to unbind; permission or driver mismatch")
            return False

        time.sleep(0.4)
        if os.path.exists(bind) and os.access(bind, os.W_OK):
            if not dry_run:
                with open(bind, "w") as f:
                    f.write(devpath)
                log(f"Wrote to bind: {devpath}")
            else:
                log(f"(dry-run) would write to bind: {devpath}")
        else:
            log("Cannot write to bind; permission or driver mismatch")
            return False

        time.sleep(0.6)
        subprocess.run(["udevadm", "trigger", "-s", "tty"], check=False)
        log(f"Driver rebind: {devpath} re-bound")
        return True
    except Exception as e:
        log(f"Driver rebind failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Simple USB rebind for FTDI DMX adapters")
    parser.add_argument("--vid", default="0403", help="Vendor ID (hex)")
    parser.add_argument("--pid", default="6001", help="Product ID (hex)")
    parser.add_argument("--serial", default="", help="Serial string to match (optional)")
    parser.add_argument("--timeout", type=float, default=5.0, help="Seconds to wait for device")
    parser.add_argument("--retries", type=int, default=2, help="Number of rebind attempts")
    parser.add_argument("--dry-run", action="store_true", help="Don't write to sysfs; only log actions")
    args = parser.parse_args()

    require_root()
    for attempt in range(1, args.retries + 1):
        log(f"Attempt {attempt}/{args.retries}")
        ok = driver_rebind(args.vid, args.pid, args.serial, timeout=args.timeout, dry_run=args.dry_run)
        if ok:
            log("Rebind successful")
            sys.exit(0)
        log("Rebind attempt failed; retrying...")
        time.sleep(0.5)
    log("All attempts failed; device not re-bound")
    sys.exit(1)


if __name__ == "__main__":
    main()
