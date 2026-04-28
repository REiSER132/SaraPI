import socket
import pyaudio
import time

# НАСТРОЙКИ
REIKA_IP = "100.x.x.x"  # IP ноута в Tailscale
PORT = 5001
RATE = 16000
CHUNK = 1024

def run():
    print(f"[📡] Стрим аудио на {REIKA_IP}:{PORT}...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    p = pyaudio.PyAudio()
    
    # Ищи ID своего INMP441 через arecord -l, обычно 1,0 или 2,0
    # Здесь берём дефолтный ввод, убедись что в alsamixer он выбран
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=RATE,
                    input=True, frames_per_buffer=CHUNK)

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
        print("\n[⏹] Аудио-стрим остановлен.")

if __name__ == "__main__":
    run()