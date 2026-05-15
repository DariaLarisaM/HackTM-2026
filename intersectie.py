import cv2
import numpy as np
from ultralytics import YOLO
import serial
import time
import math
import requests
import threading
from collections import defaultdict

model = YOLO('yolov8n.pt')
cap = cv2.VideoCapture(0)

# Zonele
roi_banda_1 = np.array([[10, 50], [280, 50], [280, 430], [10, 430]], np.int32)   
roi_centru  = np.array([[285, 120], [355, 120], [355, 360], [285, 360]], np.int32) 
roi_banda_2 = np.array([[360, 50], [630, 50], [630, 430], [360, 430]], np.int32) 

try:
    arduino = serial.Serial('COM4', 9600, timeout=0.1, write_timeout=0.1)
    time.sleep(2)
    # REZOLVAREA PROBLEMEI 2: Sincronizam Arduino la prima rulare (ii dam Verde pe Banda 1)
    arduino.write(b'N') 
    print("✅ Conectat la Arduino!")
except Exception:
    arduino = None
    print("⚠️ Rulam FARA hardware.")

stare_curenta = '1' 
stare_sistem = '1'  # Poate fi '1', '2' sau 'BLOCAT'
timp_ultima_schimbare = time.time()

TIMP_VERDE_MAXIM = 10.0 
TIMP_VERDE_MINIM = 5.0  

istoric_trasee = defaultdict(lambda: [])
viteze_curente = {}
API_URL = "http://localhost:5000/api/alerte"

def trimite_alerta_api(id_obiect, viteza, scor):
    payload = {
        "id_obiect": id_obiect,
        "viteza_kmh": round(viteza, 2),
        "probabilitate_accident": round(scor, 2),
        "timestamp": time.time()
    }
    try:
        print(f"📡 [API MOCK] Alerta accident! ID: {id_obiect} | Risc: {payload['probabilitate_accident']}%")
    except Exception as e:
        pass

print("Apasă 'q' pe video pentru ieșire.")

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break

    timp_curent = time.time()
    results = model.track(frame, persist=True, stream=True, classes=[0, 67])
    
    masini_banda_1 = 0
    masini_banda_2 = 0
    masini_centru = 0

    for r in results:
        boxes = r.boxes
        if boxes.id is not None:
            track_ids = boxes.id.int().cpu().tolist()
        else:
            track_ids = [-1] * len(boxes)

        for box, track_id in zip(boxes, track_ids):
            x1, y1, x2, y2 = int(box.xyxy[0][0]), int(box.xyxy[0][1]), int(box.xyxy[0][2]), int(box.xyxy[0][3])
            center_x, center_y = int((x1 + x2) / 2), int((y1 + y2) / 2)

            # Numărare
            if cv2.pointPolygonTest(roi_centru, (center_x, center_y), False) > 0:
                masini_centru += 1
                cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 255), 2) 
            elif cv2.pointPolygonTest(roi_banda_1, (center_x, center_y), False) > 0:
                masini_banda_1 += 1
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            elif cv2.pointPolygonTest(roi_banda_2, (center_x, center_y), False) > 0:
                masini_banda_2 += 1
                cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 165, 0), 2)
            else:
                cv2.rectangle(frame, (x1, y1), (x2, y2), (100, 100, 100), 2)

            # Viteză și accidente
            if track_id != -1:
                istoric = istoric_trasee[track_id]
                istoric.append((center_x, center_y, timp_curent))
                if len(istoric) > 10: istoric.pop(0)

                viteza_estimata = 0
                scor_accident = 0

                if len(istoric) >= 5:
                    pct_vechi, pct_nou = istoric[0], istoric[-1]
                    distanta_pixeli = math.sqrt((pct_nou[0] - pct_vechi[0])**2 + (pct_nou[1] - pct_vechi[1])**2)
                    timp_scurs = pct_nou[2] - pct_vechi[2]
                    
                    if timp_scurs > 0:
                        viteza_pixeli_sec = distanta_pixeli / timp_scurs
                        viteza_estimata = viteza_pixeli_sec * 0.15 
                        viteza_anterioara = viteze_curente.get(track_id, viteza_estimata)
                        
                        if viteza_anterioara > 30 and viteza_estimata < 5:
                            scor_accident = 85.0 
                        elif viteza_anterioara > 15 and viteza_estimata < 2:
                            scor_accident = 50.0 
                            
                        if scor_accident > 40:
                            threading.Thread(target=trimite_alerta_api, args=(track_id, viteza_anterioara, scor_accident)).start()
                            cv2.putText(frame, "⚠️ ACCIDENT!", (x1, y1 - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

                        viteze_curente[track_id] = viteza_estimata

                cv2.putText(frame, f"ID:{track_id} | {int(viteza_estimata)}km/h", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

    cv2.polylines(frame, [roi_banda_1], isClosed=True, color=(0, 255, 0), thickness=2)
    cv2.polylines(frame, [roi_centru], isClosed=True, color=(255, 0, 255), thickness=2) 
    cv2.polylines(frame, [roi_banda_2], isClosed=True, color=(255, 165, 0), thickness=2)

    # --- LOGICA: SCHIMBARE LA TERMEN + ANTI-SPAM ---
    secunde_trecute = timp_curent - timp_ultima_schimbare
    stare_dorita = stare_curenta 

    # 1. Calculam cand vrem sa schimbam starea
    if secunde_trecute >= TIMP_VERDE_MAXIM:
        stare_dorita = '2' if stare_curenta == '1' else '1'
    elif secunde_trecute >= TIMP_VERDE_MINIM:
        if stare_curenta == '1':
            if masini_banda_1 == 0 and masini_banda_2 > 0: stare_dorita = '2'
            elif masini_banda_2 > masini_banda_1 + 1: stare_dorita = '2'
        elif stare_curenta == '2':
            if masini_banda_2 == 0 and masini_banda_1 > 0: stare_dorita = '1'
            elif masini_banda_1 > masini_banda_2 + 1: stare_dorita = '1'

    # 2. Executam tranzitia DOAR in momentul schimbarii
    if stare_dorita != stare_curenta:
        if masini_centru > 0:
            # Centrul e ocupat exact in momentul schimbarii! Blocati intersectia!
            if stare_sistem != 'BLOCAT':
                stare_sistem = 'BLOCAT'
                if arduino is not None:
                    try: arduino.write(b'B') # Trimis o singura data
                    except Exception: pass
        else:
            # Centrul este liber, putem finaliza schimbarea
            stare_curenta = stare_dorita
            stare_sistem = stare_curenta
            timp_ultima_schimbare = timp_curent
            
            if arduino is not None:
                try:
                    arduino.write(b'N' if stare_sistem == '1' else b'E')
                except Exception: pass

    # --- AFIȘARE INTERFAȚĂ ---
    timp_ramas = max(0, int(TIMP_VERDE_MAXIM - secunde_trecute))
    
    cv2.putText(frame, f"Timp: {timp_ramas}s", (280, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(frame, f"B1: {masini_banda_1}", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(frame, f"Centru: {masini_centru}", (260, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2)
    cv2.putText(frame, f"B2: {masini_banda_2}", (480, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 165, 0), 2)

    if stare_sistem == '1':
        cv2.putText(frame, "VERDE: B1 | ROSU: B2", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    elif stare_sistem == '2':
        cv2.putText(frame, "ROSU: B1 | VERDE: B2", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 165, 0), 2)
    elif stare_sistem == 'BLOCAT':
        cv2.putText(frame, "URGENTA: AMBELE ROSU", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
    cv2.imshow("UrbanPulse - Intersectie", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

if arduino is not None:
    arduino.close()
cap.release()
cv2.destroyAllWindows()