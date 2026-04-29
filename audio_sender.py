import socket
import pyaudio

# === НАСТРОЙКИ ===
REIKA_IP = "reika"  # Твой Tailscale IP
PORT = 5001
RATE = 48000
CHUNK = 480  # 480 сэмплов → 10 мс (48000/480 = 100 Гц)

def run():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    p = pyaudio.PyAudio()
    
    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK,
        input_device_index=0,
        start=False
    )
    stream.start_stream()
    
    print(f"[📡] Стрим на {REIKA_IP}:{PORT} (CHUNK={CHUNK} → {CHUNK*2} байт)")
    
    try:
        while True:
            data = stream.read(CHUNK, exception_on_overflow=False)
            sock.sendto(data, (REIKA_IP, PORT))
    except KeyboardInterrupt:
        pass
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
        sock.close()

if __name__ == "__main__":
    run()