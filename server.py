from flask import Flask, request, jsonify
import sqlite3
import datetime

app = Flask(__name__)
DB_NAME = 'hacktm.db'

# --- 1. INITIALIZARE BAZA DE DATE ---
def init_db():
    """Creeaza tabelele daca nu exista deja"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Tabelul pentru Monetizare (Trafic)
    c.execute('''
        CREATE TABLE IF NOT EXISTS trafic (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            intersectie TEXT,
            banda TEXT,
            volum INTEGER,
            data_timp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabelul pentru Alerte (Accidente)
    c.execute('''
        CREATE TABLE IF NOT EXISTS alerte (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_obiect INTEGER,
            viteza REAL,
            risc REAL,
            data_timp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Baza de date 'hacktm.db' este pregatita!")

# --- 2. ENDPOINT: MONETIZARE TRAFIC ---
@app.route('/api/trafic', methods=['POST'])
def primeste_trafic():
    date_primite = request.json
    
    id_intersectie = date_primite.get('id_intersectie', 'Necunoscuta')
    benzi = date_primite.get('date_benzi', [])
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    for banda in benzi:
        nume_banda = banda.get('nume_banda')
        volum = banda.get('volum_masini_noi')
        
        # Salvam in baza de date
        c.execute("INSERT INTO trafic (intersectie, banda, volum) VALUES (?, ?, ?)", 
                  (id_intersectie, nume_banda, volum))
        
    conn.commit()
    conn.close()
    
    print(f"💰 [DB API] Am salvat date de trafic pentru {id_intersectie}!")
    return jsonify({"status": "succes", "mesaj": "Date trafic inregistrate"}), 201

# --- 3. ENDPOINT: ALERTE ACCIDENTE ---
@app.route('/api/alerte', methods=['POST'])
def primeste_alerta():
    date_primite = request.json
    
    id_obiect = date_primite.get('id_obiect')
    viteza = date_primite.get('viteza_kmh')
    risc = date_primite.get('probabilitate_accident')
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    c.execute("INSERT INTO alerte (id_obiect, viteza, risc) VALUES (?, ?, ?)", 
              (id_obiect, viteza, risc))
    
    conn.commit()
    conn.close()
    
    print(f"🚨 [DB API] ALERTA salvata in baza de date! Risc: {risc}%")
    return jsonify({"status": "succes", "mesaj": "Alerta inregistrata"}), 201


if __name__ == '__main__':
    # Initializam baza de date la pornirea serverului
    init_db()
    # Pornim serverul pe portul 5000 (localhost)
    print("🚀 Serverul Backend UrbanPulse este ONLINE!")
    app.run(host='0.0.0.0', port=5000, debug=False)