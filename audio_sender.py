import socket
import pyaudio
import struct

# === НАСТРОЙКИ ===
REIKA_IP = "reika"  # ← ЦИФРОВОЙ IP!
PORT = 5001
RATE = 48000
CHUNK = 480  # 10ms (попробуй, если трещит — ставь 960)
GAIN_DB = 35  # ← Твои +35dB

def apply_gain(data, gain_db):
    """Усиление PCM сигнала"""
    factor = 10 ** (gain_db / 20)
    samples = struct.unpack(f'{len(data)//2}h', data)
    amplified = [max(-32768, min(32767, int(s * factor))) for s in samples]
    return struct.pack(f'{len(amplified)}h', *amplified)

def run():
    print(f"[📡] Стрим на {REIKA_IP}:{PORT} (+{GAIN_DB}dB)...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    p = pyaudio.PyAudio()
    
    try:
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK,
            input_device_index=0
        )
        print(f"[🎤] Захват с устройства #0. Говори...")
        
        while True:
            data = stream.read(CHUNK, exception_on_overflow=False)
            data = apply_gain(data, GAIN_DB)  # ← Усиление!
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