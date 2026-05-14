import sounddevice as sd
import numpy as np
import time

print("Se inițializează Sistemul de Analiză Acustică...")
print("Folosim Transformata Fast-Fourier pentru a găsi impacturi metalice/sticlă.")
print("-" * 50)

sample_rate = 16000

def asculta_live(indata, frames, time_info, status):
    # Transformăm semnalul într-o listă de numere
    audio = np.squeeze(indata)
    
    # 1. Măsurăm volumul (Cât de tare este zgomotul)
    volum = np.max(np.abs(audio))
    
    # Dacă e liniște sau zgomot de fundal mic, stâlpul ignoră (reglează acest 0.15 dacă e nevoie)
    if volum < 0.15:
        return
        
    # 2. MAGIA: Trecem sunetul prin Fast Fourier Transform (extragem frecvențele)
    fft_data = np.abs(np.fft.rfft(audio))
    
    # 3. Calculăm "Haosul Acustic"
    varf_energie = np.max(fft_data)
    medie_energie = np.mean(fft_data)
    
    # Raportul ne spune cât de ascuțit sau haotic e sunetul
    factor_haos = varf_energie / (medie_energie + 1e-6)
    
    # LOGICA:
    # Vocea, pisica, câinele, fluieratul -> au note clare (Factor mare, peste 15)
    # Sticla spartă, crash-ul de mașină -> zgomot haotic, energie peste tot (Factor mic, sub 12)
    
    if factor_haos < 12.0:
        print("\n" + "💥" * 20)
        print(f"🚨 ACCIDENT / IMPACT DETECTAT! 🚨")
        print(f"📊 Volum: {volum*100:.0f}% | Grad de haos: {factor_haos:.1f}/12.0")
        print("📲 Trimitem semnal video-ului să verifice intersecția!")
        print("💥" * 20 + "\n")
        time.sleep(1.5) # Luăm pauză după un impact
    else:
        # Aici intră vocile și pisicile
        print(f"🐱 Zgomot ignorat (Pisică / Voce / Muzică). Factor: {factor_haos:.1f}")

print("✅ STÂLP PORNIT! Dă-i un crash de pe telefon (ține-l aproape și dă volumul tare).")

try:
    with sd.InputStream(samplerate=sample_rate, channels=1, blocksize=int(sample_rate * 0.5), callback=asculta_live):
        while True:
            time.sleep(0.1)
except KeyboardInterrupt:
    print("\nMicrofon oprit.")