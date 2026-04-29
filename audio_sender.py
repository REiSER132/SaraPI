import socket
import pyaudio
import time

# === НАСТРОЙКИ ===
REIKA_IP = "reika"  # ← ВПИШИ TAILSCALE IP НОУТА!
PORT = 5001
RATE = 48000  # ← 48kHz вместо 16kHz!
CHUNK = 960   # ← 20ms @ 48kHz (было 320)

def run():
    print(f"[📡] Стрим на {REIKA_IP}:{PORT}...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    p = pyaudio.PyAudio()
    
    # Индекс 0 = Google voiceHAT (INMP441)
    dev_idx = 0
    
    try:
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK,
            input_device_index=dev_idx
        )
        print(f"[🎤] Захват с устройства #{dev_idx}. Говори...")
        
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