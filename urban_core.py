import cv2
import numpy as np
from ultralytics import YOLO
import serial
import time
import sounddevice as sd
import threading
import asyncio
import websockets
import json

# ================= CONFIGURĂRI =================
PORT_ARDUINO = 'COM3'  # Schimbă cu portul tău (ex: '/dev/ttyUSB0' pe Mac/Linux)
WEBSOCKET_PORT = 8765

# ROIs (Regiuni de Interes)
roi_banda_1 = np.array([[10, 50], [300, 50], [300, 430], [10, 430]], np.int32)  # NORD-SUD
roi_banda_2 = np.array([[340, 50], [630, 50], [630, 430], [340, 430]], np.int32)  # EST-VEST
roi_centru = np.array([[300, 150], [340, 150], [340, 300], [300, 300]], np.int32)  # ZONA DE IMPACT (Mijloc)

# ================= VARIABILE GLOBALE =================
stare_curenta = 'N'  # 'N' = Nord-Sud Verde, 'E' = Est-Vest Verde
timp_ultima_schimbare = time.time()
TIMP_VERDE_MAXIM = 15.0
TIMP_VERDE_MINIM = 3.0

audio_score = 0.0
video_score = 0.0
incident_activ = False
mesaj_trafic = "Trafic normal"

# Conexiuni WebSockets
connected_clients = set()


# ================= 1. MODUL AUDIO (Rulează în fundal) =================
def asculta_live(indata, frames, time_info, status):
    global audio_score
    audio = np.squeeze(indata)
    volum = np.max(np.abs(audio))

    if volum < 0.15:
        audio_score = max(0.0, audio_score - 2.0)  # Scade treptat dacă e liniște
        return

    fft_data = np.abs(np.fft.rfft(audio))
    varf_energie = np.max(fft_data)
    medie_energie = np.mean(fft_data)
    factor_haos = varf_energie / (medie_energie + 1e-6)

    # Transformăm haosul într-un scor (Haos mic = impact metalic/sticlă = scor mare)
    if factor_haos < 12.0:
        audio_score = min(100.0, 100 - (factor_haos * 5))  # Ex: factor 8 -> scor 60%
    else:
        audio_score = max(0.0, audio_score - 2.0)


def start_audio_thread():
    stream = sd.InputStream(samplerate=16000, channels=1, blocksize=8000, callback=asculta_live)
    stream.start()


# ================= 2. MODUL WEBSOCKETS (Pentru site-ul index.html) =================
async def handler(websocket):
    connected_clients.add(websocket)
    try:
        while True:
            # Structura JSON așteptată de site
            date_site = {
                "state": "V" if stare_curenta == 'N' else "R",
                "incident": incident_activ,
                "traffic_msg": mesaj_trafic,
                "accident_accuracy": f"{int(max(audio_score, video_score))}%",
                "timestamp": time.time()
            }
            await websocket.send(json.dumps(date_site))
            await asyncio.sleep(0.5)
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        connected_clients.remove(websocket)


def start_ws_server():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    start_server = websockets.serve(handler, "localhost", WEBSOCKET_PORT)
    loop.run_until_complete(start_server)
    loop.run_forever()


# ================= 3. MODUL VIDEO & LOGICĂ PRINCIPALĂ =================
if __name__ == "__main__":
    # Pornim firele de execuție secundare
    threading.Thread(target=start_audio_thread, daemon=True).start()
    threading.Thread(target=start_ws_server, daemon=True).start()
    print("✅ Servere pornite! Se încarcă AI-ul Video...")

    model = YOLO('yolov8n.pt')
    cap = cv2.VideoCapture(0)

    try:
        arduino = serial.Serial(PORT_ARDUINO, 9600, timeout=0.1)
        time.sleep(2)
        print("✅ Conectat la Arduino!")
    except Exception:
        arduino = None
        print("⚠️ Arduino neconectat. Rulăm în mod Simulare.")

    while cap.isOpened():
        success, frame = cap.read()
        if not success: break

        results = model(frame, stream=True, classes=[0, 67])  # Detectăm doar mașini/oameni
        masini_b1 = 0
        masini_b2 = 0
        masini_centru = 0

        for r in results:
            boxes = r.boxes
            for box in boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)

                # Numărăm mașinile pe zone
                if cv2.pointPolygonTest(roi_banda_1, (cx, cy), False) > 0:
                    masini_b1 += 1
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                elif cv2.pointPolygonTest(roi_banda_2, (cx, cy), False) > 0:
                    masini_b2 += 1
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 165, 0), 2)
                elif cv2.pointPolygonTest(roi_centru, (cx, cy), False) > 0:
                    masini_centru += 1
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)  # Roșu pt zonă de risc

        # --- LOGICA DE SCOR ACCIDENT ---
        # Dacă o mașină e blocată în centrul intersecției, scorul video crește
        video_score = 80.0 if masini_centru > 0 else 0.0
        scor_total_accident = (audio_score * 0.6) + (video_score * 0.4)

        if scor_total_accident > 70.0:
            incident_activ = True
            mesaj_trafic = "🚨 ACCIDENT DETECTAT! Evitați zona. Sugerăm rute ocolitoare."
        else:
            incident_activ = False
            mesaj_trafic = "Trafic normal"

        # --- LOGICA DE TRAFIC & SEMAFOR ---
        secunde_trecute = time.time() - timp_ultima_schimbare
        stare_noua = stare_curenta

        if secunde_trecute >= TIMP_VERDE_MAXIM:
            stare_noua = 'E' if stare_curenta == 'N' else 'N'
        elif secunde_trecute >= TIMP_VERDE_MINIM:
            # REGULA CERUTĂ: Dacă e roșu pe o bandă și sunt mai mult de 3 mașini, schimbă forțat!
            if stare_curenta == 'N' and masini_b2 > 3:
                stare_noua = 'E'
                mesaj_trafic = "⚠️ Aglomerație Est-Vest. Rută ocolitoare sugerată."
            elif stare_curenta == 'E' and masini_b1 > 3:
                stare_noua = 'N'
                mesaj_trafic = "⚠️ Aglomerație Nord-Sud. Rută ocolitoare sugerată."

        # Aplicăm schimbarea hardware
        if stare_noua != stare_curenta:
            stare_curenta = stare_noua
            timp_ultima_schimbare = time.time()
            if arduino:
                arduino.write(b'N' if stare_curenta == 'N' else b'E')

        # --- AFIȘARE VIZUALĂ (Pentru Juriu) ---
        cv2.polylines(frame, [roi_banda_1], True, (0, 255, 0), 2)
        cv2.polylines(frame, [roi_banda_2], True, (255, 165, 0), 2)
        cv2.polylines(frame, [roi_centru], True, (0, 0, 255), 2)  # Cutia centrului intersecției

        cv2.putText(frame, f"Audio Acc Score: {audio_score:.1f}%", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                    (0, 255, 255), 2)
        cv2.putText(frame, f"Video Acc Score: {video_score:.1f}%", (10, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                    (0, 255, 255), 2)

        culoare_text_total = (0, 0, 255) if incident_activ else (255, 255, 255)
        cv2.putText(frame, f"TOTAL ACCIDENT: {scor_total_accident:.1f}%", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                    culoare_text_total, 2)

        cv2.putText(frame, f"Mesaj: {mesaj_trafic}", (10, 450), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        cv2.imshow("UrbanPulse - Dashboard AI", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    if arduino: arduino.close()
    cap.release()
    cv2.destroyAllWindows()