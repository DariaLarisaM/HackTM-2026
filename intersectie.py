import cv2
import numpy as np
from ultralytics import YOLO
import serial
import time

# 1. Incarcam modelul AI
model = YOLO('yolov8n.pt')

# 2. Deschidem camera AUXILIARA (Index 1). 
# Daca nu merge, pune 0 inapoi pentru cea de la laptop.
cap = cv2.VideoCapture(1)

# 3. Definim zona mare de detectie
roi_banda_1 = np.array([[50, 50], [590, 50], [590, 430], [50, 430]], np.int32)

# 4. Conectarea la Arduino (Protejata la erori)
try:
    # Aici pui COM-ul tau corect (ex: 'COM5')
    arduino = serial.Serial('COM3', 9600, timeout=0.1, write_timeout=0.1)
    time.sleep(2)
    print("✅ Conectat cu succes la Arduino!")
except Exception as e:
    arduino = None
    print("⚠️ Arduino NU este conectat. Rulam FARA hardware (doar video).")

# Variabile pentru memorie/stabilizare ca sa nu palpaie semaforul
stare_curenta = 'R'
cadre_confirmare = 0

print("Apasă tasta 'q' pe fereastra video pentru a închide camera.")

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break

    # Rulam detectia (0=persoana, 67=telefon)
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

   # 5. Logica Semforului
    stare_noua = 'V' if masini_in_zona >= 2 else 'R'

    # Stabilizarea imaginii pe ecran (sa nu palpaie textul)
    if stare_noua != stare_curenta:
        cadre_confirmare += 1
        if cadre_confirmare >= 5:
            stare_curenta = stare_noua
            cadre_confirmare = 0
    else:
        cadre_confirmare = 0

    # !!! MODIFICAREA ESTE AICI !!!
    # Trimitem continuu starea către Arduino, la fiecare cadru video.
    # Arduino se apara singur de "spam" datorita variabilei sale interne stareCurenta.
    if arduino is not None:
        try:
            if stare_curenta == 'V':
                arduino.write(b'V')
            else:
                arduino.write(b'R')
        except Exception:
            pass # Ignoram erorile temporare de cablu

    # Scriem pe ecran statusul
    if stare_curenta == 'V':
        cv2.putText(frame, "SEMAFOR: VERDE", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)
    else:
        cv2.putText(frame, "SEMAFOR: ROSU", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
    # Afisam fereastra
    cv2.imshow("UrbanPulse - AI Video", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Curatam la final
if arduino is not None:
    arduino.close()
cap.release()
cv2.destroyAllWindows()