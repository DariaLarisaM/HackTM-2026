import sounddevice as sd
import numpy as np
import time
import requests
import threading

print("Se inițializează Sistemul de Analiză Acustică...")
print("Folosim Transformata Fast-Fourier pentru a găsi impacturi metalice/sticlă.")
print("-" * 50)

sample_rate = 16000
API_AUDIO_URL = "http://localhost:5000/api/audio" # Endpoint-ul noului nostru server

def trimite_alerta_api(volum, factor_haos):
    """Trimite datele de accident audio catre backend"""
    payload = {
        "sursa": "Stalp_Inteligent_Intersecție_1",
        "volum": round(float(volum), 2),
        "factor_haos": round(float(factor_haos), 2),
        "timestamp": time.time()
    }
    try:
        requests.post(API_AUDIO_URL, json=payload, timeout=2)
        print("📡 [API] Alertă trimisă cu succes la dispecerat!")
    except Exception as e:
        print("⚠️ Eroare la comunicarea cu serverul:", e)

def asculta_live(indata, frames, time_info, status):
    # Transformăm semnalul într-o listă de numere
    audio = np.squeeze(indata)
    
    # 1. Măsurăm volumul (Cât de tare este zgomotul)
    volum = np.max(np.abs(audio))
    
    if volum < 0.15:
        return
        
    # 2. MAGIA: Trecem sunetul prin Fast Fourier Transform
    fft_data = np.abs(np.fft.rfft(audio))
    
    # 3. Calculăm "Haosul Acustic"
    varf_energie = np.max(fft_data)
    medie_energie = np.mean(fft_data)
    
    factor_haos = varf_energie / (medie_energie + 1e-6)
    
    if factor_haos < 12.0:
        print("\n" + "💥" * 20)
        print(f"🚨 ACCIDENT / IMPACT DETECTAT! 🚨")
        print(f"📊 Volum: {volum*100:.0f}% | Grad de haos: {factor_haos:.1f}/12.0")
        
        # ---> NOU: Trimitem spre API folosind un Thread ca sa nu se blocheze microfonul
        threading.Thread(target=trimite_alerta_api, args=(volum, factor_haos)).start()
        
        print("💥" * 20 + "\n")
        time.sleep(1.5) # Luăm pauză după un impact
    else:
        print(f"🐱 Zgomot ignorat (Pisică / Voce / Muzică). Factor: {factor_haos:.1f}")

print("✅ STÂLP PORNIT! Dă-i un crash de pe telefon (ține-l aproape și dă volumul tare).")

try:
    with sd.InputStream(samplerate=sample_rate, channels=1, blocksize=int(sample_rate * 0.5), callback=asculta_live):
        while True:
            time.sleep(0.1)
except KeyboardInterrupt:
    print("\nMicrofon oprit.")