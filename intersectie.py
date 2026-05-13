import cv2
import numpy as np
from ultralytics import YOLO
import serial # 1. Importăm librăria nouă
import time

# 2. Conectarea la Arduino (Atenție: 'COM3' se va schimba în funcție de laptopul tău, ex: COM4, COM5. Pe Mac/Linux este ceva de genul '/dev/ttyUSB0')
# Punem asta într-un bloc try-except ca să nu dea eroare dacă nu ai Arduino băgat în priză acum.
try:
    arduino = serial.Serial('COM3', 9600, timeout=1)
    time.sleep(2) # Așteptăm 2 secunde să se inițializeze conexiunea
    print("Conectat la Arduino!")
except:
    arduino = None
    print("Arduino nu este conectat, rulăm doar modul video.")

# Încărcăm modelul (se va descărca automat un mic fișier la prima rulare)
model = YOLO('yolov8n.pt')

# Deschidem camera web (0 este camera integrată a laptopului)
cap = cv2.VideoCapture(0)

# Definim zona de așteptare la semafor (un pătrat pe centrul ecranului)
roi_banda_1 = np.array([[200, 200], [440, 200], [440, 440], [200, 440]], np.int32)

print("Apasă tasta 'q' pe tastatură pentru a închide camera.")

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        print("Eroare la citirea camerei!")
        break

    # Căutăm DOAR persoane (clasa 0) și telefoane (clasa 67) pentru teste
    results = model(frame, stream=True, classes=[0, 67])
    
    masini_in_zona = 0

    for r in results:
        boxes = r.boxes
        for box in boxes:
            # Coordonatele cutiei obiectului
            x1, y1, x2, y2 = int(box.xyxy[0][0]), int(box.xyxy[0][1]), int(box.xyxy[0][2]), int(box.xyxy[0][3])
            
            # Centrul obiectului
            center_x = int((x1 + x2) / 2)
            center_y = int((y1 + y2) / 2)

            # Verificăm dacă centrul este în zona de așteptare
            is_inside = cv2.pointPolygonTest(roi_banda_1, (center_x, center_y), False)

            if is_inside > 0:
                masini_in_zona += 1
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2) # Verde dacă e în zonă
                cv2.circle(frame, (center_x, center_y), 5, (0, 255, 0), -1)
            else:
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2) # Roșu dacă e afară
                cv2.circle(frame, (center_x, center_y), 5, (0, 0, 255), -1)

    # Desenăm zona pe ecran
    cv2.polylines(frame, [roi_banda_1], isClosed=True, color=(255, 255, 0), thickness=2)

    # Afișăm statusul
    cv2.putText(frame, f"Obiecte in zona: {masini_in_zona}", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    # Logica de decizie!
    if masini_in_zona >= 2:
        cv2.putText(frame, "SCHIMBA SEMAFORUL -> VERDE!", (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)
        
        # 3. Trimitem semnalul către Arduino (trimitem litera 'V' de la Verde)
        if arduino is not None:
            arduino.write(b'V') 
    else:
        # Trimitem 'R' de la Roșu dacă nu sunt destule mașini
        if arduino is not None:
            arduino.write(b'R')

    cv2.imshow("UrbanPulse - Test Intersectie", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()