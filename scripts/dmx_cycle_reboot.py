import os
import time
import serial
import subprocess
import sys

# --- CONFIG ---
LEVEL = 255
FPS = 44

def log(m):
    print(time.strftime("[%H:%M:%S]"), m, flush=True)


def find_port():
    # Explicitly use /dev/ttyUSB0 only
    port = "/dev/ttyUSB0"
    if os.path.exists(port):
        return port
    return None

def wait_port(timeout=10):
    t0 = time.time()
    while time.time() - t0 < timeout:
        p = find_port()
        if p:
            return p
        time.sleep(0.25)
    return None

def send_frame(ser, levels):
    ser.break_condition = True
    time.sleep(0.0001)
    ser.break_condition = False
    time.sleep(0.000012)
    ser.write(bytes([0] + levels[:512]))

def require_root():
    if os.geteuid() != 0:
        print("This script must be run as root.")
        sys.exit(1)

def real_reboot():
    try:
        os.sync()
    except Exception:
        pass
    try:
        subprocess.run(["/bin/systemctl", "reboot", "--force"], check=False)
        time.sleep(5)
    except Exception:
        pass
    try:
        os.execv("/sbin/reboot", ["/sbin/reboot", "-f"])
    except Exception as e:
        log(f"reboot exec failed: {e}")
        sys.exit(0)

def main():
    require_root()
    log("Waiting for DMX USB port...")
    port = wait_port(10)
    if not port:
        log("No DMX USB port found!")
        sys.exit(1)
    log(f"Found DMX port: {port}")
    time.sleep(2)  # Wait for device to settle
    try:
        ser = serial.Serial(port, baudrate=250000, bytesize=8, parity='N', stopbits=2)
    except Exception as e:
        log(f"Failed to open serial port: {e}")
        sys.exit(1)
    
    log(f"Sending flashing DMX patterns at {FPS} FPS...")
    frame_delay = 1.0 / FPS
    brightness = 0
    direction = 1  # 1 for increasing, -1 for decreasing
    
    try:
        while True:
            # Flash pattern: 0 -> 255 -> 0
            levels = [brightness] * 15 + [0] * (512 - 15)
            send_frame(ser, levels)
            
            # Update brightness
            brightness += direction * 5
            if brightness >= LEVEL:
                brightness = LEVEL
                direction = -1
            elif brightness <= 0:
                brightness = 0
                direction = 1
            
            time.sleep(frame_delay)
    except KeyboardInterrupt:
        log("Interrupted. Stopping DMX transmission.")
    finally:
        ser.close()
        log("Done.")

if __name__ == "__main__":
    main()
