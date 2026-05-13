import cv2
import numpy as np
from ultralytics import YOLO
import serial
import time

# 1. Incarcam modelul AI
model = YOLO('yolov8n.pt')

# 2. Deschidem camera
cap = cv2.VideoCapture(0) # Daca ai camera pe USB, pune 1

# 3. Definim zona mare de detectie
roi_banda_1 = np.array([[50, 50], [590, 50], [590, 430], [50, 430]], np.int32)

# 4. Conectarea la Arduino
try:
    # Atentie sa fie COM-ul corect!
    arduino = serial.Serial('COM3', 9600, timeout=0.1, write_timeout=0.1)
    time.sleep(2)
    print("✅ Conectat cu succes la Arduino!")
except Exception as e:
    arduino = None
    print("⚠️ Arduino NU este conectat. Rulam FARA hardware (doar video).")

# --- Setarile pentru cronometru si logica ---
stare_curenta = 'E'
cadre_confirmare = 0
timp_ultima_schimbare = time.time()
timp_verde_normal = 10.0 # Cate secunde sta normal pe verde
timp_verde_minim = 4.0   # Timpul minim inainte sa il poata "taia" AI-ul

print("Apasă tasta 'q' pe fereastra video pentru a închide camera.")

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break

    # Rulam detectia AI
    results = model(frame, stream=True, classes=[0, 67])
    masini_in_zona = 0

    for r in results:
        boxes = r.boxes
        for box in boxes:
            x1, y1, x2, y2 = int(box.xyxy[0][0]), int(box.xyxy[0][1]), int(box.xyxy[0][2]), int(box.xyxy[0][3])
            center_x = int((x1 + x2) / 2)
            center_y = int((y1 + y2) / 2)

            is_inside = cv2.pointPolygonTest(roi_banda_1, (center_x, center_y), False)

            if is_inside > 0:
                masini_in_zona += 1
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.circle(frame, (center_x, center_y), 5, (0, 255, 0), -1)
            else:
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                cv2.circle(frame, (center_x, center_y), 5, (0, 0, 255), -1)

    cv2.polylines(frame, [roi_banda_1], isClosed=True, color=(255, 255, 0), thickness=2)
    cv2.putText(frame, f"Obiecte in zona: {masini_in_zona}", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    # 5. Logica: Timer Clasic + Inteligenta Artificiala
    timp_curent = time.time()
    timp_trecut = timp_curent - timp_ultima_schimbare
    stare_dorita = stare_curenta
    
    # Cazul 1: Suntem pe ROSU pt axa camerei (Est-Vest are verde)
    if stare_curenta == 'E':
        if timp_trecut >= timp_verde_normal:
            stare_dorita = 'N' 
        elif masini_in_zona >= 2 and timp_trecut >= timp_verde_minim:
            stare_dorita = 'N' 
            cv2.putText(frame, "AI OVERRIDE: Aglomeratie! Fortez Verde!", (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
            
    # Cazul 2: Suntem pe VERDE pt axa camerei (Nord-Sud are verde)
    elif stare_curenta == 'N':
        if timp_trecut >= timp_verde_normal:
            stare_dorita = 'E' 
        elif masini_in_zona == 0 and timp_trecut >= timp_verde_minim:
            stare_dorita = 'E' 
            cv2.putText(frame, "AI OVERRIDE: Strada libera, cedez prioritatea!", (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)

    # Stabilizarea semnalului AI
    if stare_dorita != stare_curenta:
        cadre_confirmare += 1
        if cadre_confirmare >= 5:
            stare_curenta = stare_dorita
            cadre_confirmare = 0
            timp_ultima_schimbare = timp_curent 
            print(f">>> TRIMIT COMANDA: {stare_curenta} <<<") 
    else:
        cadre_confirmare = 0

    # Trimitem starea către Arduino
    if arduino is not None:
        try:
            if stare_curenta == 'N':
                arduino.write(b'N')
            else:
                arduino.write(b'E')
        except Exception:
            pass 

    # Afisare timer pe ecran (nu il lasam sa scada sub 0)
    timp_ramas = max(0, int(timp_verde_normal - timp_trecut))
    
    if stare_curenta == 'N':
        cv2.putText(frame, f"AXA NORD-SUD: VERDE ({timp_ramas}s)", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)
    else:
        cv2.putText(frame, f"AXA EST-VEST: VERDE ({timp_ramas}s)", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 3)

    # Liniile care lipseau pentru afisarea ferestrei!
    cv2.imshow("UrbanPulse - AI Hybrid Traffic", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

if arduino is not None:
    arduino.close()
cap.release()
cv2.destroyAllWindows()