import asyncio
import json
import serial
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

app = FastAPI()

# Permitem accesul pentru Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurare Serial (Arduino)
try:
    ser = serial.Serial('COM3', 9600, timeout=1)
except:
    print("Warning: Arduino nu este conectat pe COM3. Modul simulare activat.")
    ser = None

class CityGlowBridge:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.co2_saved = 0.0 # kg calculat estimativ

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, data: dict):
        for connection in self.active_connections:
            await connection.send_json(data)

bridge = CityGlowBridge()

@app.websocket("/ws/city-data")
async def websocket_endpoint(websocket: WebSocket):
    await bridge.connect(websocket)
    try:
        while True:
            # Așteptăm date de la scriptul YOLO (via HTTP sau direct injection)
            data = await websocket.receive_text()
            # Aici putem procesa datele înainte de a le retrimite către UI
            await bridge.broadcast(json.loads(data))
    except Exception as e:
        print(f"Error: {e}")
    finally:
        bridge.disconnect(websocket)

# Endpoint pentru ca scriptul YOLO să trimită alerte de Near-Miss
@app.post("/alert/near-miss")
async def receive_near_miss(data: dict):
    # Logica de business: Calculăm riscul
    data["timestamp"] = datetime.now().strftime("%H:%M:%S")
    await bridge.broadcast({"type": "NEAR_MISS_ALERT", "payload": data})
    return {"status": "received"}

# Endpoint pentru Emergency Override (Ambulanță)
@app.post("/control/emergency")
async def emergency_override(command: dict):
    # command = {"direction": "main_street", "state": "V"}
    if ser:
        ser.write(command['state'].encode())
    
    await bridge.broadcast({
        "type": "EMERGENCY_STATUS",
        "message": f"Unda Verde activata pentru {command['direction']}"
    })
    return {"status": "Command sent to Arduino"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)