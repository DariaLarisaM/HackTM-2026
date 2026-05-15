from flask import Flask, request, jsonify
from flask_sock import Sock
import sqlite3
import datetime
import json
import base64

app = Flask(__name__)
sock = Sock(app)
DB_NAME = 'hacktm.db'

# Păstrăm conexiunile active pentru paginile web
connected_clients = []

# --- 1. INITIALIZARE BAZA DE DATE (Codul tău neschimbat) ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS trafic (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            intersectie TEXT,
            banda TEXT,
            volum INTEGER,
            data_timp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS alerte (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_obiect INTEGER,
            viteza REAL,
            risc REAL,
            data_timp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS alerte_audio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sursa TEXT,
            volum REAL,
            factor_haos REAL,
            data_timp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print("✅ Baza de date 'hacktm.db' este pregatita!")

# --- 2. ENDPOINT: MONETIZARE TRAFIC (Neschimbat) ---
@app.route('/api/trafic', methods=['POST'])
def primeste_trafic():
    date = request.json
    id_intersectie = date.get('id_intersectie', 'Necunoscuta')
    benzi = date.get('date_benzi', [])
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    for banda in benzi:
        c.execute("INSERT INTO trafic (intersectie, banda, volum) VALUES (?, ?, ?)", 
                  (id_intersectie, banda.get('nume_banda'), banda.get('volum_masini_noi')))
    conn.commit()
    conn.close()
    
    print(f"💰 [DB API] Trafic salvat pentru {id_intersectie}!")
    return jsonify({"status": "succes"}), 201

# --- 3. ENDPOINT: ALERTE VIDEO (Modificat doar cu notificare WS) ---
@app.route('/api/alerte', methods=['POST'])
def primeste_alerta():
    date = request.json
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO alerte (id_obiect, viteza, risc) VALUES (?, ?, ?)", 
              (date.get('id_obiect'), date.get('viteza_kmh'), date.get('probabilitate_accident')))
    conn.commit()
    conn.close()
    
    print(f"🚨 [DB API] ALERTA VIDEO salvata! Risc: {date.get('probabilitate_accident')}%")
    return jsonify({"status": "succes"}), 201

# --- 4. ENDPOINT: ALERTE AUDIO (Neschimbat) ---
@app.route('/api/audio', methods=['POST'])
def primeste_alerta_audio():
    date = request.json
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO alerte_audio (sursa, volum, factor_haos) VALUES (?, ?, ?)", 
              (date.get('sursa'), date.get('volum'), date.get('factor_haos')))
    conn.commit()
    conn.close()
    
    print(f"🎤 [DB API] ALERTA AUDIO salvata! Factor Haos: {date.get('factor_haos')}")
    return jsonify({"status": "succes"}), 201

# ---> NOU ENDPOINT: PRIMESTE IMAGINILE DIN BUFFER LA ACCIDENT SI LE TRIMITE PE INTERFATA
@app.route('/api/accident-buffer', methods=['POST'])
def primeste_accident_buffer():
    if 'imagini' not in request.files:
        return jsonify({"eroare": "Lipsesc imaginile"}), 400
        
    fisiere = request.files.getlist('imagini')
    imagini_base64 = []

    for f in fisiere:
        continut = f.read()
        # Transformăm imaginile în base64 pentru a le trimite instantaneu prin WebSocket pe site
        encoded = base64.b64encode(continut).decode('utf-8')
        imagini_base64.append(encoded)

    # Împingem pozele și starea de incident pe interfețe (Instituție și Cetățean)
    broadcast_ws({
        "type": "accident_event",
        "incident": True,
        "mesaj": "ACCIDENT CONFIRMAT MULTIMODAL!",
        "images": imagini_base64
    })
    
    print("📸 [SERVER] Buffer-ul de 10 poze a fost procesat și trimis live către interfețe!")
    return jsonify({"status": "succes"}), 200

# --- 5. ENDPOINT: STATUS LIVE (Păstrat neschimbat) ---
@app.route('/api/status-live', methods=['GET'])
def verifica_status_intersectie():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM alerte WHERE data_timp >= datetime('now', '-10 seconds')")
    alerte_video = c.fetchall()
    c.execute("SELECT * FROM alerte_audio WHERE data_timp >= datetime('now', '-10 seconds')")
    alerte_audio = c.fetchall()
    conn.close()

    status_intersectie = "SIGUR"
    mesaj = "Trafic normal."
    gravitate = 0

    if len(alerte_video) > 0 and len(alerte_audio) == 0:
        status_intersectie = "SUSPECT"
        mesaj = "Franare brusca detectata video. Fara sunet de impact."
        gravitate = 1
    elif len(alerte_audio) > 0 and len(alerte_video) == 0:
        status_intersectie = "SUSPECT"
        mesaj = "Zgomot puternic detectat. Posibil accident in afara razei camerei."
        gravitate = 1
    elif len(alerte_video) > 0 and len(alerte_audio) > 0:
        status_intersectie = "CRITIC"
        mesaj = "ACCIDENT CONFIRMAT MULTIMODAL! Echipajele au fost alertate."
        gravitate = 2
        
    # Trimitem statusul Live și prin WebSockets pentru sincronizarea automată a hărților
    broadcast_ws({
        "type": "status_update",
        "state": "1" if gravitate == 1 else "2",
        "incident": gravitate == 2,
        "mesaj": mesaj,
        "objects_b1": len(alerte_video),
        "objects_b2": len(alerte_audio)
    })
        
    return jsonify({
        "status": status_intersectie,
        "nivel_gravitate": gravitate,
        "mesaj": mesaj,
        "detalii_senzori": {
            "video_triggers": len(alerte_video),
            "audio_triggers": len(alerte_audio)
        }
    }), 200

# --- 6. GESTIONARE CONEXIUNI WEBSOCKET ---
@sock.route('/')
def handle_ws(ws):
    global connected_clients
    connected_clients.append(ws)
    try:
        while True:
            ws.receive()  # Păstrează socket-ul deschis
    except Exception:
        pass
    finally:
        connected_clients.remove(ws)

def broadcast_ws(data):
    message = json.dumps(data)
    for client in connected_clients[:]:
        try:
            client.send(message)
        except Exception:
            connected_clients.remove(client)

if __name__ == '__main__':
    init_db()
    print("🚀 Serverul Backend UrbanPulse rulează cu suport WebSocket live!")
    app.run(host='0.0.0.0', port=5000, debug=False)