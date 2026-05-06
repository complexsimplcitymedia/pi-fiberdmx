import os, time, threading, subprocess, csv, sys, requests, signal, atexit
from flask import Flask, render_template, redirect, url_for, flash, jsonify, Response, request, send_file
import cv2

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CSV_PATH = os.path.join(BASE_DIR, "data", "channel_map.csv")
sys.path.append(os.path.join(BASE_DIR, "scripts"))

app = Flask(__name__,
            template_folder=os.path.join(os.path.dirname(__file__), "templates"),
            static_folder=os.path.join(os.path.dirname(__file__), "logos"),
            static_url_path="/logos")
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "please-set-a-real-secret")

# Import DMX controller
from dmx_controller import DMXController

# ---------------- Status handling ----------------
STATUS_MESSAGE = "Ready"
CHANNEL_MODE = "PATTERN"  # "PATTERN" or "TOGGLE"

# Initialize DMX controller
dmx = None
try:
    dmx = DMXController(serial_port="/dev/ttyUSB0")
    dmx.connect()
    STATUS_MESSAGE = "DMX Controller Connected"
except Exception as e:
    STATUS_MESSAGE = f"DMX Error: {e}"

# Cleanup handler for system shutdown/reboot
def cleanup_on_exit():
    """Ensure all DMX channels are OFF when system shuts down"""
    if dmx:
        try:
            print("Shutting down DMX controller...")
            dmx.shutdown_all()
        except Exception as e:
            print(f"Error during DMX shutdown: {e}")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print(f"Received signal {signum}, shutting down DMX...")
    cleanup_on_exit()
    sys.exit(0)

# Register cleanup handlers
atexit.register(cleanup_on_exit)
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

def set_status(msg: str):
    global STATUS_MESSAGE
    STATUS_MESSAGE = str(msg)

@app.route("/status")
def status():
    return jsonify({
        "status": STATUS_MESSAGE,
        "channel_mode": CHANNEL_MODE
    })

# ---------------- System service control ----------------
def svc(action: str, no_block=True):
    # Functionality removed
    pass

# DMXWorker no longer needed - using DMXController directly

# Camera streaming
camera = None
camera_lock = threading.Lock()

def get_camera():
    global camera
    if camera is None:
        camera = cv2.VideoCapture(0)
        if not camera.isOpened():
            return None
    return camera

def release_camera():
    global camera
    if camera is not None:
        camera.release()
        camera = None

def generate_frames():
    """Generator function for camera feed streaming."""
    cam = get_camera()
    if cam is None:
        return

    while True:
        with camera_lock:
            ret, frame = cam.read()

        if not ret:
            break

        # Encode frame as JPEG
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n'
               b'Content-Length: ' + str(len(frame)).encode() + b'\r\n\r\n' + frame + b'\r\n')

def stop_all_processes():
    pass

def find_port():
    return "/dev/ttyUSB0"  # Dummy return

def send_frame(ser, levels):
    pass

def load_map(path=CSV_PATH):
    rows=[]
    if not os.path.exists(path): return rows
    with open(path, newline="") as f:
        first=f.readline(); f.seek(0)
        if first.lower().startswith("ch,"):
            reader = csv.DictReader((ln for ln in f if ln.strip() and not ln.lstrip().startswith("#")))
            for r in reader:
                rows.append({"ch": int(r["ch"]), "color": r["color"].strip().upper(), "digit": r["digit"].strip()})
        else:
            for ln in f:
                s=ln.strip()
                if not s or s.startswith("#"): continue
                ch,color,digit=[p.strip() for p in s.split(",")]
                rows.append({"ch": int(ch), "color": color.upper(), "digit": digit})
    rows.sort(key=lambda x: x["ch"])
    return rows

# ---------------- Wi-Fi ----------------
WIFI_BASE = os.path.join(BASE_DIR)

@app.route("/wifi", methods=["GET"])
def wifi_page():
    nets = []
    return render_template("wifi.html", nets=nets)

@app.route("/wifi/connect", methods=["POST"])
def wifi_connect():
    flash("Wi-Fi functionality disabled")
    return redirect(url_for("wifi_page"))

@app.route("/wifi/status", methods=["GET"])
def wifi_status():
    flash("Wi-Fi functionality disabled")
    return redirect(url_for("wifi_page"))

# ---------------- Main UI ----------------
@app.route("/simple/<int:ch>/<cmd>", methods=["POST"])
def simple_onoff(ch, cmd):
    flash("Button functionality disabled")
    return redirect(url_for("index"))


# ---------------- Splash Screen ----------------
@app.route("/splash", methods=["GET"])
def splash():
    return render_template("splash.html")


@app.route("/", methods=["GET"])
def index():
    mapping = load_map()
    quick = {m["ch"]: (m["color"], m["digit"]) for m in mapping}
    
    # Check if Remote View (CH15) is active
    show_camera = False
    if dmx:
        with dmx.state_lock:
            show_camera = dmx.channel_states[15].brightness > 0
    
    return render_template("index.html", quick=quick, status=STATUS_MESSAGE,
                         channel_mode=CHANNEL_MODE, channel_mode_text=CHANNEL_MODE,
                         show_camera=show_camera)

@app.route("/video_feed")
def video_feed():
    """Stream video from webcam when Remote View is active."""
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

def play_all():
    flash("Button functionality disabled")
    return redirect(url_for("index"))

@app.route("/play/<int:ch>", methods=["POST"])
def play_ch(ch):
    """
    Dual mode for channels 1-6:
    - PATTERN mode: Run Morse pattern (loop indefinitely)
    - TOGGLE mode: Indefinite ON/OFF (for VFL testing)

    Channels 7-12: Always run Morse patterns
    
    SAFETY INTERLOCK: VIS (1-6) and IR (7-12) cannot run simultaneously.
    """
    if not dmx:
        flash("DMX controller not initialized")
        return redirect(url_for("index"))

    try:
        # Check if this channel is already running - if so, stop it
        if ch in dmx.running_patterns:
            dmx.pattern_stop(ch)  # Stop only this channel
            set_status(f"✓ Stopped pattern on Channel {ch}")
            return redirect(url_for("index"))
        
        # SAFETY: Mutual exclusion between VIS (1-6) and IR (7-12)
        if 1 <= ch <= 6:
            # Activating VIS channels - stop any IR patterns first (immediate stop)
            ir_running = [c for c in list(dmx.running_patterns.keys()) if 7 <= c <= 12]
            if ir_running:
                for ir_ch in ir_running:
                    dmx.pattern_stop(ir_ch)
            
            # Channels 1-6: Behavior depends on CHANNEL_MODE
            if CHANNEL_MODE == "PATTERN":
                # Pattern mode: Run Morse pattern (click again to stop)
                dmx.pattern_run(ch, loop_indefinitely=True)
                set_status(f"▶ Running Morse pattern on Channel {ch} (VIS) - Click again to stop")
            else:  # TOGGLE mode
                # Toggle mode: Indefinite ON/OFF
                dmx.manual_toggle(ch)
                with dmx.state_lock:
                    state = dmx.channel_states[ch]
                    if state.brightness > 0:
                        set_status(f"● Channel {ch} ON (Manual VFL mode)")
                    else:
                        set_status(f"○ Channel {ch} OFF")
        elif 7 <= ch <= 12:
            # Activating IR channels - stop all VIS patterns first (immediate stop)
            vis_running = [c for c in list(dmx.running_patterns.keys()) if 1 <= c <= 6]
            if vis_running:
                for vis_ch in vis_running:
                    dmx.pattern_stop(vis_ch)
            
            # Channels 7-12: Always run patterns
            dmx.pattern_run(ch, loop_indefinitely=True)
            set_status(f"▶ Running Morse pattern on Channel {ch} (IR) - Click again to stop")
        else:
            flash(f"Invalid channel {ch}")
    except Exception as e:
        flash(f"Error: {e}")
        set_status(f"Error CH{ch}: {e}")

    return redirect(url_for("index"))

@app.route("/sweep", methods=["POST"])
@app.route("/sweep/<int:cycles>", methods=["POST"])
def sweep(cycles=1):
    """Sequential channel test - each channel flashes individually

    Args:
        cycles: Number of cycles per channel (default 1)
    """
    # Read cycles from form data if provided
    if request.form.get('loops'):
        try:
            cycles = int(request.form.get('loops'))
        except (ValueError, TypeError):
            pass  # Keep default
    
    if not dmx:
        flash("DMX controller not initialized")
        return redirect(url_for("index"))

    try:
        dmx.sequential_test(cycles_per_channel=cycles)
        set_status(f"▶ Sequential test started: CH1-12 will flash individually ({cycles} cycle{'s' if cycles != 1 else ''} each)")
    except Exception as e:
        flash(f"Error: {e}")
        set_status(f"✗ Error starting sequential test: {e}")

    return redirect(url_for("index"))

@app.route("/channel_mode_toggle", methods=["POST"])
def channel_mode_toggle():
    """Toggle between PATTERN and TOGGLE modes for channels 1-6"""
    global CHANNEL_MODE

    if CHANNEL_MODE == "PATTERN":
        CHANNEL_MODE = "TOGGLE"
        set_status("✓ Mode changed: CH 1-6 now in TOGGLE mode (Manual ON/OFF for VFL testing)")
    else:
        CHANNEL_MODE = "PATTERN"
        set_status("✓ Mode changed: CH 1-6 now in PATTERN mode (Morse code sequences)")

    return redirect(url_for("index"))

@app.route("/flash_vis", methods=["POST"])
def flash_vis():
    """Flash all visible channels (1-6) - runs all 6 patterns together for testing"""
    if not dmx:
        flash("DMX controller not initialized")
        return redirect(url_for("index"))

    try:
        # SAFETY: Stop all IR patterns first
        ir_running = [c for c in dmx.running_patterns.keys() if 7 <= c <= 12]
        if ir_running:
            for ir_ch in ir_running:
                dmx.pattern_stop(ir_ch)
        
        # Start all VIS patterns (1-6)
        for ch in range(1, 7):
            if ch not in dmx.running_patterns:
                dmx.pattern_run(ch, loop_indefinitely=True)
        
        set_status("▶ Flash VIS: Running Morse patterns on all channels 1-6 simultaneously")
    except Exception as e:
        flash(f"Error: {e}")
        set_status(f"✗ Error during Flash VIS: {e}")

    return redirect(url_for("index"))

@app.route("/flash_ir", methods=["POST"])
def flash_ir():
    """Flash all infrared channels (7-12) - runs all 6 patterns together for testing"""
    if not dmx:
        flash("DMX controller not initialized")
        return redirect(url_for("index"))

    try:
        # SAFETY: Stop all VIS patterns first
        vis_running = [c for c in dmx.running_patterns.keys() if 1 <= c <= 6]
        if vis_running:
            for vis_ch in vis_running:
                dmx.pattern_stop(vis_ch)
        
        # Start all IR patterns (7-12)
        for ch in range(7, 13):
            if ch not in dmx.running_patterns:
                dmx.pattern_run(ch, loop_indefinitely=True)
        
        set_status("▶ Flash IR: Running Morse patterns on all channels 7-12 simultaneously")
    except Exception as e:
        flash(f"Error: {e}")
        set_status(f"✗ Error during Flash IR: {e}")

    return redirect(url_for("index"))
@app.route("/stop", methods=["POST"])
def stop():
    """Emergency stop all channels"""
    if not dmx:
        flash("DMX controller not initialized")
        return redirect(url_for("index"))

    try:
        dmx.emergency_stop()
        set_status("■ EMERGENCY STOP: All channels 1-12 stopped")
    except Exception as e:
        flash(f"Error: {e}")
        set_status(f"✗ Error during emergency stop: {e}")

    return redirect(url_for("index"))

@app.route("/shutdown", methods=["POST"])
def shutdown():
    """System shutdown - kill all DMX channels including camera"""
    if not dmx:
        flash("DMX controller not initialized")
        return redirect(url_for("index"))
    
    try:
        # First, shut down DMX channels safely
        if dmx:
            try:
                dmx.emergency_stop()  # Stop all patterns
                dmx.shutdown_all()    # Turn off all channels
            except Exception as dmx_error:
                print(f"DMX shutdown error: {dmx_error}")
        
        # Send real shutdown command to system
        # Use systemctl poweroff which is more reliable in kiosk mode
        subprocess.Popen(["sudo", "systemctl", "poweroff"], 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        set_status("System shutdown initiated...")
        flash("Shutting down safely...")
    except Exception as e:
        set_status(f"✗ Error during shutdown: {e}")
        flash(f"Shutdown failed: {e}")
    return redirect(url_for("index"))

# ---------------- Custom Toggles ----------------
TOGGLE_STATE = {13: False, 14: False, 15: False}

@app.route("/ols", methods=["POST"])
def toggle_ols():
    """Toggle OLS (channel 13) - ON/OFF only, no patterns"""
    if not dmx:
        flash("DMX controller not initialized")
        return redirect(url_for("index"))

    try:
        dmx.manual_toggle(13)  # Toggle between ON and OFF
        with dmx.state_lock:
            state = dmx.channel_states[13]
            if state.brightness > 0:
                set_status("✓ OLS (CH13) activated")
            else:
                set_status("✓ OLS (CH13) deactivated")
    except Exception as e:
        flash(f"Error: {e}")
        set_status(f"✗ Error toggling OLS: {e}")

    return redirect(url_for("index"))

@app.route("/otdr", methods=["POST"])
def toggle_otdr():
    """Toggle OTDR (channel 14) - ON/OFF only, no patterns"""
    if not dmx:
        flash("DMX controller not initialized")
        return redirect(url_for("index"))

    try:
        dmx.manual_toggle(14)  # Toggle between ON and OFF
        with dmx.state_lock:
            state = dmx.channel_states[14]
            if state.brightness > 0:
                set_status("✓ OTDR (CH14) activated")
            else:
                set_status("✓ OTDR (CH14) deactivated")
    except Exception as e:
        flash(f"Error: {e}")
        set_status(f"✗ Error toggling OTDR: {e}")

    return redirect(url_for("index"))

@app.route("/remote_view", methods=["POST"])
def toggle_remote_view():
    """Toggle Remote View (channel 15) - ON/OFF only, no patterns"""
    if not dmx:
        flash("DMX controller not initialized")
        return redirect(url_for("index"))

    try:
        dmx.manual_toggle(15)  # Toggle between ON and OFF
        with dmx.state_lock:
            state = dmx.channel_states[15]
            if state.brightness > 0:
                set_status("✓ Remote View (CH15) activated - Camera feed enabled")
            else:
                set_status("✓ Remote View (CH15) deactivated - Camera feed disabled")
    except Exception as e:
        flash(f"Error: {e}")
        set_status(f"✗ Error toggling Remote View: {e}")

    return redirect(url_for("index"))


# ----------------  Tailscale Eyepiece - Remote Monitoring ----------------
@app.route("/api/eyepiece/status", methods=["GET"])
def eyepiece_status():
    """
    Tailscale remote monitoring endpoint - JSON status feed
    Accessible from any device on the Tailscale network
    """
    try:
        # Get Tailscale status
        tailscale_output = subprocess.check_output(['tailscale', 'status'], text=True)
        tailscale_lines = tailscale_output.strip().split('\n')

        # Parse Tailscale status
        ts_ip = None
        ts_status = "unknown"
        for line in tailscale_lines:
            if 'laser-dmx' in line.lower():
                parts = line.split()
                if parts:
                    ts_ip = parts[0]
                    ts_status = "connected"
                    break

        # Get system info
        uptime = subprocess.check_output(['uptime', '-p'], text=True).strip()
        cpu_count = os.cpu_count()

        # Get memory info
        try:
            # Security: No user input is passed to this subprocess call (safe)
            mem_info = subprocess.check_output(['free', '-h'], text=True)
            mem_lines = mem_info.strip().split('\n')
            mem_total = mem_lines[1].split()[1] if len(mem_lines) > 1 else "N/A"
            mem_used = mem_lines[1].split()[2] if len(mem_lines) > 1 else "N/A"
        except (subprocess.CalledProcessError, IndexError):
            mem_total = "N/A"
            mem_used = "N/A"

        # Get network info
        try:
            ip_addr = subprocess.check_output(['hostname', '-I'], text=True).strip()
        except subprocess.CalledProcessError:
            ip_addr = "N/A"


        # Check if DMX UI is running (us)
        dmx_ui_port = 8080

        return jsonify({
            "timestamp": time.time(),
            "name": "laser-dmx",
            "tailscale": {
                "ip": ts_ip or "100.110.82.25",
                "status": ts_status,
                "endpoint": f"http://{ts_ip or '100.110.82.25'}"
            },
            "system": {
                "uptime": uptime,
                "cpu_cores": cpu_count,
                "memory": {
                    "total": mem_total,
                    "used": mem_used
                },
                "network_ip": ip_addr
            },
            "services": {
                "dmx_ui": {
                    "port": dmx_ui_port,
                    "status": "running",
                    "url": f"http://0.0.0.0:{dmx_ui_port}"
                },
                "qlcplus": {
                    "status": "running" if qlcplus_running else "stopped"
                }
            },
            "last_status_message": STATUS_MESSAGE
        })
    except Exception as e:
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500


@app.route("/eyepiece", methods=["GET"])
def eyepiece_dashboard():
    """
    Tailscale eyepiece dashboard - HTML view for remote monitoring
    """
    return render_template("eyepiece.html", app_title="Laser DMX - Eyepiece Monitor")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
