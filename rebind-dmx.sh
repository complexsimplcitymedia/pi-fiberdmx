#!/usr/bin/env bash
# Minimal USB rebind helper for FTDI/DMX adapters (user-writable project root)
# Run with sudo. This script is a focused extraction of the Python 'driver_rebind' logic.
set -euo pipefail

log() { printf "[%s] %s\n" "$(date '+%H:%M:%S')" "$*"; }

usage() {
  cat <<EOF
Usage: $0 [-v VID] [-p PID] [-s SERIAL] [-t TIMEOUT] [-r RETRIES] [-n]
  -v VID   USB vendor id (hex), default 0403
  -p PID   USB product id (hex), default 6001
  -s SERIAL device serial string to match (optional)
  -t TIMEOUT seconds to wait while searching for device (default 5)
  -r RETRIES number of rebind attempts (default 2)
  -n       dry-run (do not write to sysfs)
EOF
  exit 1
}

# Defaults
VID="0403"
PID="6001"
SERIAL=""
TIMEOUT=5
RETRIES=2
DRYRUN=0

while getopts ":v:p:s:t:r:nh" opt; do
  case "$opt" in
    v) VID="$OPTARG" ;;
    p) PID="$OPTARG" ;;
    s) SERIAL="$OPTARG" ;;
    t) TIMEOUT="$OPTARG" ;;
    r) RETRIES="$OPTARG" ;;
    n) DRYRUN=1 ;;
    h) usage ;;
    :) echo "Missing argument for -$OPTARG"; usage ;;
    ?) echo "Unknown option: -$OPTARG"; usage ;;
  esac
done

if [[ $EUID -ne 0 ]]; then
  log "This script must be run as root (sudo)."
  exit 2
fi

log "rebind-dmx: VID=${VID} PID=${PID} SERIAL='${SERIAL}' TIMEOUT=${TIMEOUT}s RETRIES=${RETRIES}"

# Load kernel modules (best-effort)
log "Ensuring usbserial & ftdi_sio modules are loaded"
modprobe usbserial >/dev/null 2>&1 || true
modprobe ftdi_sio >/dev/null 2>&1 || true

# Optional: write new_id to ftdi_sio driver so the device is claimed by the usb-serial driver
NEW_ID_PATH="/sys/bus/usb-serial/drivers/ftdi_sio/new_id"
if [[ -w "$NEW_ID_PATH" ]]; then
  if [[ $DRYRUN -eq 0 ]]; then
    echo "${VID} ${PID}" > "$NEW_ID_PATH" || log "warning: new_id write failed"
    log "Wrote new_id -> ${VID} ${PID}"
  else
    log "(dry-run) would write new_id -> ${VID} ${PID}"
  fi
else
  log "new_id path not writable or not present: ${NEW_ID_PATH} (continuing)"
fi

udevadm trigger -s tty >/dev/null 2>&1 || true
sleep 0.4

find_device() {
  local dir v p s
  for dir in /sys/bus/usb/devices/*; do
    if [[ -f "$dir/idVendor" && -f "$dir/idProduct" ]]; then
      v=$(<"$dir/idVendor")
      p=$(<"$dir/idProduct")
      if [[ "${v,,}" == "${VID,,}" && "${p,,}" == "${PID,,}" ]]; then
        if [[ -n "$SERIAL" ]]; then
          if [[ -f "$dir/serial" ]]; then
            s=$(<"$dir/serial")
            [[ "$s" == "$SERIAL" ]] || continue
          else
            continue
          fi
        fi
        echo "${dir##*/}"
        return 0
      fi
    fi
  done
  return 1
}

attempt=1
while [[ $attempt -le $RETRIES ]]; do
  log "Attempt ${attempt} of ${RETRIES}: searching for device"
  devpath=""
  t0=$(date +%s)
  while [[ -z "$devpath" && $(( $(date +%s) - t0 )) -lt $TIMEOUT ]]; do
    if devpath=$(find_device); then
      break
    fi
    sleep 0.25
  done

  if [[ -z "$devpath" ]]; then
    log "Device not found (VID=${VID}, PID=${PID}, SERIAL='${SERIAL}')"
    attempt=$((attempt+1))
    sleep 0.5
    continue
  fi

  log "Found device sysfs id: ${devpath}"

  if [[ $DRYRUN -eq 1 ]]; then
    log "(dry-run) would unbind/bind ${devpath} and re-trigger udev"
    exit 0
  fi

  UNBIND=/sys/bus/usb/drivers/usb/unbind
  BIND=/sys/bus/usb/drivers/usb/bind
  if [[ -w "$UNBIND" && -w "$BIND" ]]; then
    log "Unbinding ${devpath}"
    echo "$devpath" > "$UNBIND" || { log "unbind write failed"; attempt=$((attempt+1)); sleep 0.5; continue; }
    sleep 0.4
    log "Binding ${devpath}"
    echo "$devpath" > "$BIND" || { log "bind write failed"; attempt=$((attempt+1)); sleep 0.5; continue; }
    sleep 0.6
    udevadm trigger -s tty >/dev/null 2>&1 || true
    log "Rebind appears to have completed for ${devpath}"
    ls -l /dev/ttyUSB* /dev/dmx-usb* 2>/dev/null || true
    exit 0
  else
    log "Cannot write to unbind/bind sysfs paths: ${UNBIND} or ${BIND} (permission/driver mismatch)"
    exit 3
  fi
done

log "All attempts exhausted; device not re-bound."
exit 4
