import cv2
import numpy as np
from ultralytics import YOLO
import serial
import time
import math
import json
import websocket  # pip install websocket-client
import threading
from collections import defaultdict

# --- CONFIGURARE ---
model = YOLO('yolov8n.pt')
# Adăugăm cv2.CAP_DSHOW pentru a forța deschiderea camerei pe Windows rapid
import os

# --- ÎNLOCUIEȘTE SECȚIUNEA DE DESCHIDERE CAMERĂ CU ASTA ---
os.environ["OPENCV_VIDEOIO_MSMF_ENABLE_HW_TRANSFORMS"] = "0"

# Încercăm indexul 1 (camera externă) fără DSHOW mai întâi, apoi cu el
cap = cv2.VideoCapture(1) 

if not cap.isOpened():
    print("⚠️ Index 1 eșuat, încercăm Index 1 cu DSHOW...")
    cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)

if not cap.isOpened():
    print("⚠️ Index 1 eșuat complet, încercăm Index 2...")
    cap = cv2.VideoCapture(2, cv2.CAP_DSHOW)

# IMPORTANT: Setăm buffer-ul la 1 pentru a avea zero latență (esențial pentru AI real-time)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
# --------------------------------------------------------

if not cap.isOpened():
    print("❌ Camera tot nu pornește. Trecem pe modul SIMULARE VIDEO.")
    # SOLUȚIA DE URGENȚĂ: Dacă nu ai cameră, folosește un video de test de pe net
    # cap = cv2.VideoCapture("https://traffic_video_sample.mp4")

if not cap.isOpened():
    print("❌ Eroare: Nu pot accesa camera. Verifică dacă e folosită de alt program.")

# Factori de conversie pentru Product Innovation
# Estimare: O masina la ralanti produce ~2.3kg CO2 pe ora. 
# Salvăm CO2 reducând timpul de așteptare la semafor.
CO2_PER_SECOND_IDLE = 0.00064 # kg/s per masina

# Zonele (Păstrate din codul tău)
roi_banda_1 = np.array([[10, 50], [280, 50], [280, 430], [10, 430]], np.int32)
roi_centru  = np.array([[285, 120], [355, 120], [355, 360], [285, 360]], np.int32)
roi_banda_2 = np.array([[360, 50], [630, 50], [630, 430], [360, 430]], np.int32)

# Comunicare Hardware
try:
    arduino = serial.Serial('COM3', 9600, timeout=0.1)
    time.sleep(2)
    arduino.write(b'N') 
    print("✅ Hardware Serial sincronizat!")
except:
    arduino = None
    print("⚠️ Mod SIMULARE (Fara Arduino)")

# Comunicare Bridge (WebSocket)
ws = None
def connect_ws():
    global ws
    try:
        ws = websocket.create_connection("ws://localhost:8000/ws/city-data")
        print("✅ Conectat la City Glow Bridge!")
    except:
        print("❌ Bridge-ul nu este pornit. Porneste cityglow_bridge.py mai intai.")

threading.Thread(target=connect_ws, daemon=True).start()

# State management
stare_sistem = '1'
timp_ultima_schimbare = time.time()
total_co2_saved = 0.0
istoric_trasee = defaultdict(lambda: [])
viteze_curente = {}

def send_to_bridge(msg_type, payload):
    if ws:
        try:
            ws.send(json.dumps({"type": msg_type, "payload": payload}))
        except: pass

while cap.isOpened():
    success, frame = cap.read()
    if not success: break

    timp_curent = time.time()
    # Adaugam track=True pentru a pastra ID-urile intre frame-uri
    results = model.track(frame, persist=True, verbose=False, classes=[2, 3, 5, 7]) # Masini, moto, bus, truck

    masini_banda_1 = 0
    masini_banda_2 = 0
    masini_centru = 0

    for r in results:
        boxes = r.boxes
        if boxes.id is not None:
            track_ids = boxes.id.int().cpu().tolist()
            for box, track_id in zip(boxes, track_ids):
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

                # Logica ROI & Desenare
                in_b1 = cv2.pointPolygonTest(roi_banda_1, (cx, cy), False) > 0
                in_b2 = cv2.pointPolygonTest(roi_banda_2, (cx, cy), False) > 0
                in_ctr = cv2.pointPolygonTest(roi_centru, (cx, cy), False) > 0

                if in_ctr: masini_centru += 1
                elif in_b1: masini_banda_1 += 1
                elif in_b2: masini_banda_2 += 1

                # Analiza Near-Miss & Viteza
                istoric = istoric_trasee[track_id]
                istoric.append((cx, cy, timp_curent))
                if len(istoric) > 10: istoric.pop(0)

                if len(istoric) >= 5:
                    d = math.sqrt((cx-istoric[0][0])**2 + (cy-istoric[0][1])**2)
                    dt = timp_curent - istoric[0][2]
                    viteza = (d / dt) * 0.15
                    
                    v_veche = viteze_curente.get(track_id, viteza)
                    # Detectie Near-Miss (Decelerare brusca > 20km/h intr-o fractiune de secunda)
                    if v_veche > 25 and viteza < 5:
                        send_to_bridge("NEAR_MISS", {"id": track_id, "v_init": v_veche, "pos": [cx, cy]})
                        cv2.putText(frame, "!!! NEAR MISS !!!", (x1, y1-40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 3)

                    viteze_curente[track_id] = viteza
                    cv2.putText(frame, f"ID:{track_id} {int(viteza)}km/h", (x1, y1-10), 0, 0.5, (255,255,255), 2)

    # Logica de business: Calcul CO2 salvat
    # Daca avem masini la rosu si le dam verde mai repede decat ciclul standard
    if stare_sistem == '1': 
        # Banda 2 sta la rosu. Daca o eliberam, salvam CO2.
        total_co2_saved += masini_banda_2 * CO2_PER_SECOND_IDLE

    # --- LOGICA SEMAFORIZARE PROACTIVA ---
    # (Păstrăm structura ta, dar trimitem datele către Dashboard)
    secunde_trecute = timp_curent - timp_ultima_schimbare
    
    # Broadcast catre Command Center la fiecare secunda
    if int(timp_curent * 10) % 10 == 0:
        send_to_bridge("TRAFFIC_STATS", {
            "b1": masini_banda_1,
            "b2": masini_banda_2,
            "co2": round(total_co2_saved, 4),
            "state": stare_sistem
        })

    # Logica de schimbare (Simplified for demo)
    if secunde_trecute > 5 and masini_banda_2 > masini_banda_1 + 2 and stare_sistem == '1':
        if masini_centru == 0:
            stare_sistem = '2'
            timp_ultima_schimbare = timp_curent
            if arduino: arduino.write(b'E')

    # UI Overlay
    cv2.imshow("City Glow - AI Core", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.release()
cv2.destroyAllWindows()