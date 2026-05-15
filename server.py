from flask import Flask, request, jsonify
import sqlite3
import datetime

app = Flask(__name__)
DB_NAME = 'hacktm.db'

# --- 1. INITIALIZARE BAZA DE DATE ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Tabelul pentru Trafic (Monetizare)
    c.execute('''
        CREATE TABLE IF NOT EXISTS trafic (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            intersectie TEXT,
            banda TEXT,
            volum INTEGER,
            data_timp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabelul pentru Alerte Video
    c.execute('''
        CREATE TABLE IF NOT EXISTS alerte (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_obiect INTEGER,
            viteza REAL,
            risc REAL,
            data_timp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # ---> NOU: Tabelul pentru Alerte Audio (Stalpul Inteligent)
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
    print("✅ Baza de date 'hacktm.db' este pregatita si contine tabelul AUDIO!")

# --- 2. ENDPOINT: MONETIZARE TRAFIC ---
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

# --- 3. ENDPOINT: ALERTE VIDEO ---
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

# ---> NOU: 4. ENDPOINT: ALERTE AUDIO (STALP)
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

if __name__ == '__main__':
    init_db()
    print("🚀 Serverul Backend UrbanPulse este ONLINE!")
    app.run(host='0.0.0.0', port=5000, debug=False)
    
@app.route('/api/status-live', methods=['GET'])
def verifica_status_intersectie():
    """
    Acest API este apelat de Site-ul web in continuu (ex: o data pe secunda).
    Compara alertele din baza de date pentru a confirma un accident real.
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # 1. Cautam alerte VIDEO in ultimele 10 secunde
    c.execute("""
        SELECT * FROM alerte 
        WHERE data_timp >= datetime('now', '-10 seconds')
    """)
    alerte_video = c.fetchall()
    
    # 2. Cautam alerte AUDIO in ultimele 10 secunde
    c.execute("""
        SELECT * FROM alerte_audio 
        WHERE data_timp >= datetime('now', '-10 seconds')
    """)
    alerte_audio = c.fetchall()
    conn.close()

    # --- LOGICA DE COMPARARE ---
    status_intersectie = "SIGUR" # Default
    mesaj = "Trafic normal."
    gravitate = 0

    if len(alerte_video) > 0 and len(alerte_audio) == 0:
        status_intersectie = "SUSPECT"
        mesaj = "Franare brusca detectata video. Fara sunet de impact."
        gravitate = 1 # Galben pe site

    elif len(alerte_audio) > 0 and len(alerte_video) == 0:
        status_intersectie = "SUSPECT"
        mesaj = "Zgomot puternic detectat. Posibil accident in afara razei camerei."
        gravitate = 1 # Galben pe site

    elif len(alerte_video) > 0 and len(alerte_audio) > 0:
        # MAGIA: Avem confirmare din DOUA surse!
        status_intersectie = "CRITIC"
        mesaj = "ACCIDENT CONFIRMAT MULTIMODAL! Echipajele au fost alertate."
        gravitate = 2 # ROSU intermitent pe site
        
    return jsonify({
        "status": status_intersectie,
        "nivel_gravitate": gravitate,
        "mesaj": mesaj,
        "detalii_senzori": {
            "video_triggers": len(alerte_video),
            "audio_triggers": len(alerte_audio)
        }
    }), 200