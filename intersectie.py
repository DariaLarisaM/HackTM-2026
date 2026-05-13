import cv2
import numpy as np
from ultralytics import YOLO
import serial
import time

model = YOLO('yolov8n.pt')
cap = cv2.VideoCapture(0)

roi_banda_1 = np.array([[10, 50], [300, 50], [300, 430], [10, 430]], np.int32)   
roi_banda_2 = np.array([[340, 50], [630, 50], [630, 430], [340, 430]], np.int32) 

try:
    arduino = serial.Serial('COM3', 9600, timeout=0.1, write_timeout=0.1)
    time.sleep(2)
    print("✅ Conectat la Arduino!")
except Exception:
    arduino = None
    print("⚠️ Rulam FARA hardware.")

# --- VARIABILE PENTRU TIMP ---
stare_curenta = '1' 
timp_ultima_schimbare = time.time() # Memorăm momentul în care a pornit programul

# Setările timer-ului (le poți ajusta pentru prezentarea de la hackathon)
TIMP_VERDE_MAXIM = 10.0 # Se schimbă automat după 10 secunde
TIMP_VERDE_MINIM = 3.0  # Semaforul nu poate fi schimbat mai devreme de 3 secunde

print("Apasă 'q' pe video pentru ieșire.")

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break

    results = model(frame, stream=True, classes=[0, 67])
    masini_banda_1 = 0
    masini_banda_2 = 0

    for r in results:
        boxes = r.boxes
        for box in boxes:
            x1, y1, x2, y2 = int(box.xyxy[0][0]), int(box.xyxy[0][1]), int(box.xyxy[0][2]), int(box.xyxy[0][3])
            center_x, center_y = int((x1 + x2) / 2), int((y1 + y2) / 2)

            if cv2.pointPolygonTest(roi_banda_1, (center_x, center_y), False) > 0:
                masini_banda_1 += 1
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            elif cv2.pointPolygonTest(roi_banda_2, (center_x, center_y), False) > 0:
                masini_banda_2 += 1
                cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 165, 0), 2)

    cv2.polylines(frame, [roi_banda_1], isClosed=True, color=(0, 255, 0), thickness=2)
    cv2.polylines(frame, [roi_banda_2], isClosed=True, color=(255, 165, 0), thickness=2)

    # --- LOGICA HIBRIDĂ (TIMP + AI) ---
    timp_curent = time.time()
    secunde_trecute = timp_curent - timp_ultima_schimbare
    stare_noua = stare_curenta

    # Regula 1: A expirat timpul maxim? Trecem la celălalt semafor.
    if secunde_trecute >= TIMP_VERDE_MAXIM:
        stare_noua = '2' if stare_curenta == '1' else '1'
    
    # Regula 2: Nu a expirat timpul maxim, dar a trecut cel minim. AI-ul are voie să intervină.
    elif secunde_trecute >= TIMP_VERDE_MINIM:
        if stare_curenta == '1':
            # Dacă B1 are verde, dar e goală, și pe B2 așteaptă cineva -> Dăm verde la B2 imediat
            if masini_banda_1 == 0 and masini_banda_2 > 0:
                stare_noua = '2'
            # Sau dacă B2 s-a aglomerat tare (are mai multe mașini decât B1)
            elif masini_banda_2 > masini_banda_1 + 1:
                 stare_noua = '2'
                 
        elif stare_curenta == '2':
            # Dacă B2 are verde, dar e goală, și pe B1 așteaptă cineva -> Dăm verde la B1 imediat
            if masini_banda_2 == 0 and masini_banda_1 > 0:
                stare_noua = '1'
            elif masini_banda_1 > masini_banda_2 + 1:
                 stare_noua = '1'

    # Aplicăm schimbarea și resetăm cronometrul
    if stare_noua != stare_curenta:
        stare_curenta = stare_noua
        timp_ultima_schimbare = time.time()

    # Comunicare Arduino
    if arduino is not None:
        try:
            arduino.write(b'1' if stare_curenta == '1' else b'2')
        except Exception:
            pass 

    # --- AFIȘARE INTERFAȚĂ ---
    # Afișăm și un cronometru vizual ca să vedeți logica în acțiune
    timp_ramas = max(0, int(TIMP_VERDE_MAXIM - secunde_trecute))
    
    cv2.putText(frame, f"Timp: {timp_ramas}s", (280, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(frame, f"B1 (Stanga): {masini_banda_1}", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(frame, f"B2 (Dreapta): {masini_banda_2}", (350, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 165, 0), 2)

    if stare_curenta == '1':
        cv2.putText(frame, "VERDE: B1 | ROSU: B2", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    else:
        cv2.putText(frame, "ROSU: B1 | VERDE: B2", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 165, 0), 2)
        
    cv2.imshow("UrbanPulse - Intersectie Hibrida", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

if arduino is not None:
    arduino.close()
cap.release()
cv2.destroyAllWindows()