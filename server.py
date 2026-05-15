from flask import Flask, jsonify, request
from flask_cors import CORS
import time

app = Flask(__name__)
CORS(app) # Permitem site-ului web să ceară date

# Starea centrală a sistemului
stare_sistem = {
    "audio_confirmat": False,
    "video_confirmat": False,
    "accident_major": False,
    "mesaj_alerta": "Trafic normal. Nu sunt raportate incidente."
}

@app.route('/api/alerte', methods=['POST'])
def primeste_alerta():
    date = request.json
    sursa = date.get("sursa")
    
    if sursa == "audio":
        print("🟢 DISPECER: Am primit confirmare AUDIO (Impact detectat)!")
        stare_sistem["audio_confirmat"] = True
        
    elif sursa == "video":
        print("🔵 DISPECER: Am primit confirmare VIDEO (Blocaj detectat)!")
        stare_sistem["video_confirmat"] = True

    # Logica de fuziune: Accident confirmat doar dacă ambii senzori au detectat ceva
    if stare_sistem["audio_confirmat"] and stare_sistem["video_confirmat"]:
        if not stare_sistem["accident_major"]:
            print("🚨🚨🚨 DISPECER: ACCIDENT MAJOR CONFIRMAT! TRIMIT LA SITE! 🚨🚨🚨")
        stare_sistem["accident_major"] = True
        stare_sistem["mesaj_alerta"] = "⚠️ ACCIDENT GRAV CONFIRMAT! (Impact acustic + Blocaj video detectat). Echipajele de urgență au fost alertate."

    return jsonify({"status": "Alerta primita"}), 200

@app.route('/api/status', methods=['GET'])
def trimite_status():
    return jsonify(stare_sistem), 200

@app.route('/api/reset', methods=['GET'])
def reset_sistem():
    stare_sistem["audio_confirmat"] = False
    stare_sistem["video_confirmat"] = False
    stare_sistem["accident_major"] = False
    stare_sistem["mesaj_alerta"] = "Trafic normal. Nu sunt raportate incidente."
    print("♻️ DISPECER: Sistem resetat.")
    return jsonify({"status": "Resetat"}), 200

if __name__ == '__main__':
    print("📞 DISPECERUL 112 A PORNIT (Port 5000)...")
    app.run(port=5000, debug=False)