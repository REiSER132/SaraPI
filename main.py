import time, math, sys, signal, json, threading
from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from luma.core.render import canvas
import paho.mqtt.client as mqtt
import emotions
import face_renderer

# --- КОНФИГ ---
MQTT_BROKER = "pizero"  # IP брокера в Tailscale (или 127.0.0.1 если локально)
MQTT_PORT = 1883
MQTT_TOPIC = "sara/face/command"
CLIENT_ID = "SaraPI_Face_v7.5"

target_lock = threading.Lock()
target = emotions.presets["idle"].copy()

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"[📡] MQTT: подключено к {MQTT_BROKER}:{MQTT_PORT}")
        client.subscribe(MQTT_TOPIC, qos=1)
    else:
        print(f"[❌] MQTT: отказ в подключении, код {rc}")

def on_message(client, userdata, msg):
    try:
        cmd = json.loads(msg.payload.decode())
        emo = cmd.get("emotion", "idle")
        vol = float(cmd.get("volume", 0.0))
        
        with target_lock:
            # Применяем пресет, кроме рта (им управляет аудио)
            if emo in emotions.presets:
                for k, v in emotions.presets[emo].items():
                    if k != "mouth_open":
                        target[k] = v
            
            # EMA-фильтр для липсинка (сглаживает рывки TTS)
            raw_mouth = max(0.0, min(2.5, vol * 2.5))
            alpha = 0.18  # 0.15-0.25: меньше = плавнее, больше = отзывчивее
            prev_mouth = target["mouth_open"]
            target["mouth_open"] = prev_mouth * (1 - alpha) + raw_mouth * alpha
            
    except Exception as e:
        print(f"[⚠️] MQTT payload error: {e}")

# Инициализация MQTT
mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=CLIENT_ID)
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.reconnect_delay_set(min_delay=1, max_delay=60)
mqtt_client.username_pw_set("", "") # Если брокер без авторизации

# Сигналы
def sig_handler(sig, frame):
    print('\n[⏹] Shutdown. Выключаем Сару.')
    sys.exit(0)
signal.signal(signal.SIGINT, sig_handler)

print("[🔌] Init I2C & SSD1306...")
try:
    serial = i2c(port=1, address=0x3C)
    device = ssd1306(serial)
except Exception as e:
    print(f"[❌] OLED Error: {e}"); sys.exit(1)

# Запуск MQTT в фоне
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
mqtt_client.loop_start()

TARGET_FPS = 60
frame_time = 1.0 / TARGET_FPS
frame_count = 0
fps_start = time.perf_counter()

print("[▶] Engine v7.5 LIVE. Жду JSON на MQTT.")

while True:
    loop_start = time.perf_counter()
    
    # Lerp с локом
    with target_lock:
        for k in emotions.state:
            emotions.state[k] = emotions.lerp(emotions.state[k], target[k], 0.15)

    # Дыхание + микро-дрожание зрачков
    t = time.time()
    breath = math.sin(t * 1.5) * 1.0
    el = emotions.state["eye_openness"] + math.sin(t*2.1)*0.03
    er = emotions.state["eye_openness"] + math.sin(t*1.9)*0.03
    
    blink = (t % 4.0) > 3.8
    el = 0.05 if blink else el
    er = 0.05 if blink else er

    # Рендер
    with canvas(device) as draw:
        face_renderer.render_face(draw, emotions.state, breath, el, er)
        frame_count += 1
        fps = frame_count / (time.perf_counter() - fps_start)
        draw.text((110, 54), f"{fps:.0f}", fill="white")

    # Контроль FPS без перегрузки CPU
    elapsed = time.perf_counter() - loop_start
    sleep_time = max(0.0, frame_time - elapsed)
    time.sleep(sleep_time)