CITY GLOW — versiune bazată pe intersectie.py ORIGINAL

Important:
- intersectie.py NU este modificat.
- cityglow_bridge.py rulează fișierul original și doar interceptează informațiile pe care acesta deja le produce:
  - V / R trimis către Arduino
  - textul "Obiecte in zona: X"
  - textul "SEMAFOR: VERDE" / "SEMAFOR: ROSU"

Fișiere:
- index.html
- style.css
- script.js
- cityglow_bridge.py
- intersectie.py  -> copia ta originală, nemodificată
- requirements.txt
- README.txt

Cum rulezi:
1. Instalează dependențele:
   pip install -r requirements.txt

2. Verifică în intersectie.py portul Arduino:
   serial.Serial('COM3', 9600, ...)
   Dacă Arduino e pe alt port, schimbi DOAR la tine în intersectie.py dacă era deja necesar pentru hardware.

3. Pornește bridge-ul:
   python cityglow_bridge.py

4. Deschide site-ul cu Live Server în VS Code:
   index.html -> Open with Live Server

5. Site-ul se conectează la:
   ws://localhost:8765

Cum se sincronizează:
- intersectie.py detectează obiecte video.
- intersectie.py decide starea:
  - V dacă sunt minimum 2 obiecte în zonă
  - R altfel
- intersectie.py trimite V/R către Arduino.
- cityglow_bridge.py interceptează aceeași stare V/R.
- script.js actualizează harta, cele două semafoare, dashboard-ul, incidentul și notificările.

Conturi instituție locale:
- politie@cityglow.ro / inst123
- primarie@cityglow.ro / admin123

Conturi cetățean demo:
- cetatean1@cityglow.ro / city123
- cetatean2@cityglow.ro / glow123

Cetățenii pot crea cont local în browser cu localStorage.
Nu este necesară bază de date.
