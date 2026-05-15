"""
CITY GLOW BRIDGE — Conectează Intersectia AI cu platforma Web (index.html)
"""
import asyncio
import json
import re
import runpy
import threading
import time
from pathlib import Path

import cv2
import serial
import websockets

WEBSOCKET_HOST = "localhost"
WEBSOCKET_PORT = 8765
ORIGINAL_FILE = "intersectie.py"

clients = set()
state_lock = threading.Lock()

# Starea centrală care este trimisă către frontend
latest_state = {
    "source": "original-intersectie.py",
    "intersection": "Bd. Take Ionescu × Str. Michelangelo",
    "city": "Timișoara",
    "objects_b1": 0,
    "objects_b2": 0,
    "state": "1", # 1 pt Banda 1 Verde, 2 pt Banda 2 Verde
    "incident": False,
    "crew_status": "standby",
    "timestamp": time.time()
}

OriginalSerial = serial.Serial
original_putText = cv2.putText

def update_state_from_light(light_state):
    """Actualizează ce bandă are verde (N = Banda 1, E = Banda 2)"""
    global latest_state
    state_val = "1" if light_state == "N" else "2"
    with state_lock:
        latest_state.update({
            "state": state_val,
            "timestamp": time.time()
        })

def update_state_from_objects(b1, b2):
    """Actualizează aglomerația și detectează incidente (ex: blocaj masiv)"""
    global latest_state
    with state_lock:
        # Generăm o alertă în Dashboard dacă sunt peste 4 mașini pe o bandă
        is_incident = (b1 >= 4 or b2 >= 4)
        latest_state.update({
            "objects_b1": b1,
            "objects_b2": b2,
            "incident": is_incident,
            "crew_status": "în drum" if is_incident else "standby",
            "timestamp": time.time()
        })

class CityGlowSerialProxy:
    """Interceptează comunicarea cu Arduino"""
    def __init__(self, *args, **kwargs):
        self._serial = OriginalSerial(*args, **kwargs)

    def write(self, data):
        try:
            if data == b"N":
                update_state_from_light("N")
            elif data == b"E":
                update_state_from_light("E")
        except Exception:
            pass
        return self._serial.write(data)

    def __getattr__(self, name):
        return getattr(self._serial, name)

def patched_putText(img, text, org, fontFace, fontScale, color, thickness=None, lineType=None, bottomLeftOrigin=None):
    """Interceptează statisticile desenate pe ecran de OpenCV"""
    try:
        if isinstance(text, str):
            # Căutăm mașinile de pe Banda 1
            match_b1 = re.search(r"B1 \(Stanga\):\s*(\d+)", text)
            if match_b1:
                b1_count = int(match_b1.group(1))
                update_state_from_objects(b1_count, latest_state.get("objects_b2", 0))

            # Căutăm mașinile de pe Banda 2
            match_b2 = re.search(r"B2 \(Dreapta\):\s*(\d+)", text)
            if match_b2:
                b2_count = int(match_b2.group(1))
                update_state_from_objects(latest_state.get("objects_b1", 0), b2_count)

            # Detectăm culoarea semaforului direct din text (dacă hardware-ul nu e conectat)
            if "VERDE: B1" in text:
                update_state_from_light("N")
            elif "VERDE: B2" in text:
                update_state_from_light("E")
    except Exception:
        pass

    # Returnăm funcția originală ca textul să apară și pe videoclipul live
    if bottomLeftOrigin is not None:
        return original_putText(img, text, org, fontFace, fontScale, color, thickness, lineType, bottomLeftOrigin)
    if lineType is not None:
        return original_putText(img, text, org, fontFace, fontScale, color, thickness, lineType)
    if thickness is not None:
        return original_putText(img, text, org, fontFace, fontScale, color, thickness)
    return original_putText(img, text, org, fontFace, fontScale, color)

async def websocket_handler(websocket):
    clients.add(websocket)
    try:
        with state_lock:
            await websocket.send(json.dumps(latest_state))
        async for _ in websocket:
            pass
    finally:
        clients.discard(websocket)

async def broadcast_loop():
    while True:
        await asyncio.sleep(0.15)
        if not clients:
            continue
        with state_lock:
            payload = json.dumps(latest_state)
        disconnected = []
        for client in list(clients):
            try:
                await client.send(payload)
            except Exception:
                disconnected.append(client)
        for client in disconnected:
            clients.discard(client)

async def start_websocket_server():
    print(f"🌐 City Glow Bridge pornit pe ws://{WEBSOCKET_HOST}:{WEBSOCKET_PORT}")
    async with websockets.serve(websocket_handler, WEBSOCKET_HOST, WEBSOCKET_PORT):
        await broadcast_loop()

def start_server_thread():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_websocket_server())

def run_original_intersectie():
    original_path = Path(ORIGINAL_FILE)
    if not original_path.exists():
        print(f"❌ EROARE: Pune cityglow_bridge.py în același folder cu {ORIGINAL_FILE}!")
        return

    # Aplicăm interceptările
    serial.Serial = CityGlowSerialProxy
    cv2.putText = patched_putText

    print("✅ Conectare reușită. Se lansează AI-ul video...")
    runpy.run_path(str(original_path), run_name="__main__")

if __name__ == "__main__":
    server_thread = threading.Thread(target=start_server_thread, daemon=True)
    server_thread.start()
    time.sleep(0.5)
    run_original_intersectie()