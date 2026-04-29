import socket
import pyaudio
import time
import sys

# === НАСТРОЙКИ ===
REIKA_IP = "reika"  # ← ВПИШИ СЮДА TAILSCALE IP НОУТА!
PORT = 5001
RATE = 32000
CHUNK = 320  # 20ms @ 16kHz (важно для webrtcvad на приёмнике)

def find_inmp441(p):
    """Ищет устройство с INMP441 или первое доступное input"""
    for i in range(p.get_device_count()):
        dev = p.get_device_info_by_index(i)
        name = dev['name'].lower()
        if dev['maxInputChannels'] > 0:
            if 'inmp' in name or 'usb' in name or 'digital' in name:
                print(f"[🎤] Нашёл микрофон: {dev['name']} (idx={i})")
                return i
    # Если не нашли — берём первый доступный input
    for i in range(p.get_device_count()):
        dev = p.get_device_info_by_index(i)
        if dev['maxInputChannels'] > 0:
            print(f"[⚠️] INMP441 не найден, беру дефолт: {dev['name']} (idx={i})")
            return i
    raise RuntimeError("Нет устройств ввода!")

def run():
    print(f"[📡] Стрим на {REIKA_IP}:{PORT}...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    p = pyaudio.PyAudio()
    dev_idx = 0
    
    try:
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=RATE,
                        input=True, frames_per_buffer=CHUNK,
                        input_device_index=dev_idx)
        print("[▶] Стрим запущен. Говори...")
        
        while True:
            data = stream.read(CHUNK, exception_on_overflow=False)
            sock.sendto(data, (REIKA_IP, PORT))
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"\n[❌] Ошибка: {e}")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
        sock.close()
        print("\n[⏹] Стрим остановлен.")

if __name__ == "__main__":
    run()