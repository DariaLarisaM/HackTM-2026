import cv2
import numpy as np
import serial
import time
import requests
import threading
import math

# --- CONFIGURARE CULORI DEMO (HSV) ---
arie_minima_obiect = 500 

# 1. Roșu
rosu_low_1 = np.array([0, 100, 100])
rosu_high_1 = np.array([10, 255, 255])
rosu_low_2 = np.array([160, 100, 100])
rosu_high_2 = np.array([180, 255, 255])

# 2. Alb
alb_low = np.array([0, 0, 180])
alb_high = np.array([180, 50, 255])

# 3. Galben Albicios / Deschis
galben_low = np.array([20, 30, 180])
galben_high = np.array([40, 130, 255])

# --- Setup Cameră ---
cap = cv2.VideoCapture(2) 

# Zonele tale
roi_banda_1 = np.array([[220, 10], [420, 10], [420, 470], [220, 470]], np.int32) 
roi_centru  = np.array([[220, 140], [420, 140], [420, 340], [220, 340]], np.int32) 
roi_banda_2 = np.array([[10, 140], [630, 140], [630, 340], [10, 340]], np.int32) 

# --- Setup Arduino & State ---
try:
    arduino = serial.Serial('COM4', 9600, timeout=0.1, write_timeout=0.1)
    time.sleep(2)
    arduino.write(b'N') 
    print("✅ Conectat la Arduino!")
except Exception:
    arduino = None
    print("⚠️ Rulam FARA hardware.")

stare_curenta = '1' 
stare_sistem = '1'  
timp_ultima_schimbare = time.time()
TIMP_VERDE_MAXIM = 10.0 
TIMP_VERDE_MINIM = 3.0  

# --- SETĂRI API ---
API_TRAFIC_URL = "http://localhost:5000/api/trafic" 

vehicule_detectate_b1 = 0
vehicule_detectate_b2 = 0
timp_ultimul_raport_trafic = time.time()
INTERVAL_RAPORTARE_TRAFIC = 10.0 
ID_INTERSECTIE = "Intersectie_Demo_Rapid" 

# GLOBALE PENTRU TRACKING VITEZĂ
istoric_centre = [] 
DISTANTA_MAX_TRACKING = 60 # Pixeli maximi între cadre pentru a considera că e aceeași mașină

def trimite_date_monetizare(volum_b1, volum_b2, stare_sem): # Am adăugat parametrul stare_sem
    if volum_b1 == 0 and volum_b2 == 0: return 
    payload = {
        "id_intersectie": ID_INTERSECTIE,
        "timestamp": time.time(),
        "stare_semafor": stare_sem, # Trimitem starea semaforului către Flask
        "date_benzi": [
            {"nume_banda": "Banda_1_Nord", "volum_masini_noi": volum_b1},
            {"nume_banda": "Banda_2_Est", "volum_masini_noi": volum_b2}
        ]
    }
    try:
        requests.post(API_TRAFIC_URL, json=payload, timeout=1)
    except Exception: pass

print("Apasă 'q' pentru ieșire. Demo Mode Activ (Culori + Viteză).")

# ==========================================
# BUCLA PRINCIPALĂ DE PROCESARE A IMAGINII
# ==========================================
while cap.isOpened():
    success, frame = cap.read()
    if not success: 
        break
    
    timp_curent = time.time()
    blurred_frame = cv2.GaussianBlur(frame, (5, 5), 0)
    hsv_frame = cv2.cvtColor(blurred_frame, cv2.COLOR_BGR2HSV)

    # --- 1. Creare Măști Culori ---
    mask_r1 = cv2.inRange(hsv_frame, rosu_low_1, rosu_high_1)
    mask_r2 = cv2.inRange(hsv_frame, rosu_low_2, rosu_high_2)
    mask_rosu = cv2.bitwise_or(mask_r1, mask_r2)
    mask_alb = cv2.inRange(hsv_frame, alb_low, alb_high)
    mask_galben = cv2.inRange(hsv_frame, galben_low, galben_high)

    # --- 2. Găsire Contururi ---
    contours_rosu, _ = cv2.findContours(mask_rosu, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours_alb, _ = cv2.findContours(mask_alb, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours_galben, _ = cv2.findContours(mask_galben, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    obiecte_detectate = [] 

    # --- 3. Filtrare și Adăugare Obiecte ---
    for cnt in contours_rosu:
        if cv2.contourArea(cnt) > arie_minima_obiect:
            x, y, w, h = cv2.boundingRect(cnt)
            obiecte_detectate.append((x, y, w, h))

    for cnt in contours_alb:
        if cv2.contourArea(cnt) > arie_minima_obiect:
            x, y, w, h = cv2.boundingRect(cnt)
            obiecte_detectate.append((x, y, w, h))

    for cnt in contours_galben:
        if cv2.contourArea(cnt) > arie_minima_obiect:
            x, y, w, h = cv2.boundingRect(cnt)
            obiecte_detectate.append((x, y, w, h))

    masini_banda_1 = 0
    masini_banda_2 = 0
    masini_centru = 0

    centre_curente_noi = []

    # --- 4. Logica de Tracking Viteză & Intersecție ---
    for (x, y, w, h) in obiecte_detectate:
        cx, cy = int(x + w/2), int(y + h/2)
        color_box = (100, 100, 100) # Gri default
        
        # Logica zonelor
        if cv2.pointPolygonTest(roi_centru, (cx, cy), False) > 0:
            masini_centru += 1
            color_box = (255, 0, 255) 
        elif cv2.pointPolygonTest(roi_banda_1, (cx, cy), False) > 0:
            masini_banda_1 += 1
            vehicule_detectate_b1 += 1 
            color_box = (0, 255, 0) 
        elif cv2.pointPolygonTest(roi_banda_2, (cx, cy), False) > 0:
            masini_banda_2 += 1
            vehicule_detectate_b2 += 1 
            color_box = (255, 165, 0) 
            
        # Logica mini-tracker pentru viteză
        viteza_estimata = 0
        dist_min = float('inf')
        match_vechi = None
        
        for vechi in istoric_centre:
            dist = math.sqrt((cx - vechi['cx'])**2 + (cy - vechi['cy'])**2)
            if dist < dist_min and dist < DISTANTA_MAX_TRACKING:
                dist_min = dist
                match_vechi = vechi
                
        if match_vechi:
            timp_scurs = timp_curent - match_vechi['timp']
            if timp_scurs > 0:
                viteza_px_s = dist_min / timp_scurs
                viteza_estimata = viteza_px_s * 0.15 # Factor arbitrar pt a parea realist in km/h
                # Netezire viteză ca să nu sară numerele prea tare
                viteza_estimata = (viteza_estimata + match_vechi['viteza']) / 2 

        centre_curente_noi.append({'cx': cx, 'cy': cy, 'timp': timp_curent, 'viteza': viteza_estimata})

        # Desenăm cutia și VITEZA (Fără textul de culoare)
        cv2.rectangle(frame, (x, y), (x + w, y + h), color_box, 2)
        if viteza_estimata > 2: # Afișează doar dacă se mișcă puțin
            cv2.putText(frame, f"{int(viteza_estimata)} km/h", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color_box, 2)

    istoric_centre = centre_curente_noi # Salvăm pentru cadrul următor

    # --- 5. Desenare Zone ---
    cv2.polylines(frame, [roi_banda_1], True, (0, 255, 0), 2)
    cv2.polylines(frame, [roi_centru], True, (255, 0, 255), 2) 
    cv2.polylines(frame, [roi_banda_2], True, (255, 165, 0), 2)

    # --- 6. Raportare Monetizare (Acum trimite si starea semaforului) ---
    if timp_curent - timp_ultimul_raport_trafic >= INTERVAL_RAPORTARE_TRAFIC:
        threading.Thread(target=trimite_date_monetizare, args=(vehicule_detectate_b1, vehicule_detectate_b2, stare_sistem)).start()
        timp_ultimul_raport_trafic = timp_curent
        vehicule_detectate_b1 = 0 
        vehicule_detectate_b2 = 0

    # --- 7. Logica Semafor ---
    secunde_trecute = timp_curent - timp_ultima_schimbare
    stare_dorita = stare_curenta 

    if secunde_trecute >= TIMP_VERDE_MAXIM:
        stare_dorita = '2' if stare_curenta == '1' else '1'
    elif secunde_trecute >= TIMP_VERDE_MINIM:
        if stare_curenta == '1':
            if masini_banda_1 == 0 and masini_banda_2 > 0: stare_dorita = '2'
            elif masini_banda_2 > masini_banda_1 + 1: stare_dorita = '2'
        elif stare_curenta == '2':
            if masini_banda_2 == 0 and masini_banda_1 > 0: stare_dorita = '1'
            elif masini_banda_1 > masini_banda_2 + 1: stare_dorita = '1'

    if stare_dorita != stare_curenta:
        if masini_centru > 0:
            if stare_sistem != 'BLOCAT':
                stare_sistem = 'BLOCAT'
                if arduino is not None:
                    try: arduino.write(b'B') 
                    except Exception: pass
        else:
            stare_curenta = stare_dorita
            stare_sistem = stare_curenta
            timp_ultima_schimbare = timp_curent
            if arduino is not None:
                try: arduino.write(b'N' if stare_sistem == '1' else b'E')
                except Exception: pass

    # --- 8. UI Info pe ecran ---
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
        
    cv2.imshow("UrbanPulse - Demo Mode", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

if arduino is not None:
    arduino.close()
cap.release()
cv2.destroyAllWindows()