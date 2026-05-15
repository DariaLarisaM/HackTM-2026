import sounddevice as sd
import numpy as np
import time
import json
import websocket # pip install websocket-client
import threading

# --- CONFIGURARE ---
SAMPLE_RATE = 16000
BLOCK_SIZE = int(SAMPLE_RATE * 0.5) # Analizăm ferestre de 0.5 secunde
BRIDGE_WS_URL = "ws://localhost:8000/ws/city-data"

print("🏙️ City Glow | Audio Threat Detection System")
print("Sistem inițializat. Se caută frecvențe de impact (sticla/metal)...")

# --- CONEXIUNE BRIDGE ---
ws = None
def connect_ws():
    global ws
    try:
        ws = websocket.create_connection(BRIDGE_WS_URL)
        print("✅ Audio AI conectat la Central Bridge!")
    except Exception as e:
        print(f"⚠️ Bridge neconectat: {e}. Porniți cityglow_bridge.py!")

threading.Thread(target=connect_ws, daemon=True).start()

def send_audio_alert(volum, haos):
    if ws:
        payload = {
            "type": "AUDIO_THREAT",
            "payload": {
                "alert_type": "IMPACT_DETECTED",
                "volume": float(round(volum, 2)),
                "chaos_factor": float(round(haos, 2)),
                "timestamp": time.strftime("%H:%M:%S")
            }
        }
        try:
            ws.send(json.dumps(payload))
        except:
            print("❌ Eroare trimitere semnal către Bridge.")

def callback_audio(indata, frames, time_info, status):
    audio = np.squeeze(indata)
    volum = np.max(np.abs(audio))
    
    # Prag de liniște (ajustabil în funcție de zgomotul de fundal din sala de hackathon)
    if volum < 0.12:
        return
        
    # FFT pentru analiza frecvențelor
    fft_data = np.abs(np.fft.rfft(audio))
    varf_energie = np.max(fft_data)
    medie_energie = np.mean(fft_data)
    
    factor_haos = varf_energie / (medie_energie + 1e-6)
    
    # LOGICA DE DETECȚIE
    # Impactul (sticlă, tablă) este "zgomot alb" (haos mic, sub 12)
    # Vocea/Muzica este armonică (haos mare, peste 15)
    if factor_haos < 11.5:
        print(f"\n🚨 [DETECȚIE] IMPACT! Vol: {volum:.2f} | Haos: {factor_haos:.1f}")
        send_audio_alert(volum, factor_haos)
        # Blocăm procesarea scurt timp pentru a nu trimite 100 de alerte pentru același bufnet
        time.sleep(1) 
    else:
        # Debug opțional
        # print(f"☁️ Zgomot ambiental. Factor: {factor_haos:.1f}")
        pass

# --- START ---
try:
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, 
                        blocksize=BLOCK_SIZE, callback=callback_audio):
        print("🎤 Microfon activ. Monitorizare în curs...")
        while True:
            time.sleep(0.1)
except KeyboardInterrupt:
    print("\nSistem oprit de utilizator.")
except Exception as e:
    print(f"Eroare critică: {e}")