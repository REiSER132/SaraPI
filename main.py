import socket, json, threading, time, math, sys, signal
from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from luma.core.render import canvas
import emotions
import face_renderer

HOST, PORT = '0.0.0.0', 5000
target_lock = threading.Lock()
target = emotions.presets["idle"].copy()
last_cmd_time = time.time()

def tcp_listener():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((HOST, PORT))
    srv.listen(1)
    srv.settimeout(2.0)
    print(f"[📡] TCP Socket: {HOST}:{PORT}")
    
    while True:
        try:
            conn, addr = srv.accept()
            data = conn.recv(512).decode('utf-8').strip()
            if not data: 
                conn.close(); continue
                
            try:
                cmd = json.loads(data)
                emo = cmd.get("emotion", "idle")
                vol = float(cmd.get("volume", 0.0))
                
                with target_lock:
                    if emo in emotions.presets:
                        # Берём пресет, но не ломаем динамические параметры
                        for k, v in emotions.presets[emo].items():
                            if k != "mouth_open": target[k] = v
                    # Липсинк: маппинг 0..1 -> 0..2.5 (подстроено под кривую рта)
                    target["mouth_open"] = max(0.0, min(2.5, vol * 2.5))
                    
                conn.sendall(b"OK")
                last_cmd_time = time.time()
            except Exception as e:
                print(f"[!] JSON error: {e}")
            finally:
                conn.close()
        except socket.timeout:
            continue

def sig_handler(sig, frame):
    print('\n[⏹] Shutdown.')
    sys.exit(0)
signal.signal(signal.SIGINT, sig_handler)

print("[🔌] Init I2C & SSD1306...")
try:
    serial = i2c(port=1, address=0x3C)
    device = ssd1306(serial)
except Exception as e:
    print(f"[❌] OLED Error: {e}"); sys.exit(1)

threading.Thread(target=tcp_listener, daemon=True).start()

frame_count = 0
fps_start = time.time()
print("[▶] Engine v7.4 LIVE. Жду JSON на порту 5000.")

while True:
    t = time.time()
    
    # Lerp с блокировкой от гонки потоков
    with target_lock:
        for k in emotions.state:
            emotions.state[k] = emotions.lerp(emotions.state[k], target[k], 0.15)

    # Физика дыхания и моргания
    breath = math.sin(t * 1.5) * 1.0
    el = emotions.state["eye_openness"] + math.sin(t*2.1)*0.03
    er = emotions.state["eye_openness"] + math.sin(t*1.9)*0.03
    blink = (t % 4.0) > 3.8
    el = 0.05 if blink else el
    er = 0.05 if blink else er

    with canvas(device) as draw:
        face_renderer.render_face(draw, emotions.state, breath, el, er)
        frame_count += 1
        fps = frame_count / (t - fps_start)
        draw.text((110, 54), f"{fps:.0f}", fill="white")
        
    time.sleep(0.005)