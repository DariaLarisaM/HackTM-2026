"""
CITY GLOW BRIDGE — NU modifică intersectie.py

Rulează fișierul tău original intersectie.py exact așa cum este,
dar interceptează local informațiile pe care el deja le produce:

1. serial.Serial.write(b'V') / serial.Serial.write(b'R')
   -> site-ul primește starea semaforului.

2. cv2.putText(..., "Obiecte in zona: X", ...)
   -> site-ul primește numărul de obiecte detectate.

3. cv2.putText(..., "SEMAFOR: VERDE/ROSU", ...)
   -> site-ul primește starea semaforului chiar și dacă Arduino nu e conectat.

Site-ul se conectează la:
ws://localhost:8765

Important:
- Nu edita intersectie.py.
- Pune acest fișier în același folder cu intersectie.py.
- Rulează: python cityglow_bridge.py
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

latest_state = {
    "source": "original-intersectie.py",
    "intersection": "Bd. Take Ionescu × Str. Michelangelo",
    "city": "Timișoara",
    "objects_in_zone": 0,
    "state": "R",
    "main_light": "red",
    "secondary_light": "green",
    "incident": False,
    "crew_status": "standby",
    "timestamp": time.time()
}

OriginalSerial = serial.Serial
original_putText = cv2.putText


def update_state_from_light(light_state):
    """light_state: 'V' sau 'R'."""
    global latest_state

    state = "V" if light_state == "V" else "R"

    with state_lock:
        objects = latest_state.get("objects_in_zone", 0)

        latest_state.update({
            "state": state,
            "main_light": "green" if state == "V" else "red",
            "secondary_light": "red" if state == "V" else "green",
            "incident": state == "V" or objects >= 2,
            "crew_status": "în drum" if (state == "V" or objects >= 2) else "standby",
            "timestamp": time.time()
        })


def update_state_from_objects(objects_count):
    """objects_count vine din textul afișat de intersectie.py: Obiecte in zona: X."""
    global latest_state

    with state_lock:
        state = latest_state.get("state", "R")

        latest_state.update({
            "objects_in_zone": objects_count,
            "incident": state == "V" or objects_count >= 2,
            "crew_status": "în drum" if (state == "V" or objects_count >= 2) else "standby",
            "timestamp": time.time()
        })


class CityGlowSerialProxy:
    """
    Proxy peste serial.Serial.
    intersectie.py crede că vorbește direct cu Arduino,
    dar noi copiem local mesajele V/R pentru website.
    """

    def __init__(self, *args, **kwargs):
        self._serial = OriginalSerial(*args, **kwargs)

    def write(self, data):
        try:
            if data == b"V":
                update_state_from_light("V")
            elif data == b"R":
                update_state_from_light("R")
        except Exception:
            pass

        return self._serial.write(data)

    def __getattr__(self, name):
        return getattr(self._serial, name)


def patched_putText(img, text, org, fontFace, fontScale, color, thickness=None, lineType=None, bottomLeftOrigin=None):
    """
    Ascultă textele pe care intersectie.py deja le desenează pe frame.
    Nu schimbă logica video.
    """

    try:
        if isinstance(text, str):
            match = re.search(r"Obiecte in zona:\s*(\d+)", text)
            if match:
                update_state_from_objects(int(match.group(1)))

            if "SEMAFOR: VERDE" in text:
                update_state_from_light("V")
            elif "SEMAFOR: ROSU" in text or "SEMAFOR: ROȘU" in text:
                update_state_from_light("R")
    except Exception:
        pass

    # Păstrăm comportamentul original OpenCV.
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
        print(f"❌ Nu găsesc {ORIGINAL_FILE}. Pune cityglow_bridge.py în același folder cu intersectie.py.")
        return

    # Patch-uri locale, fără să modificăm fișierul intersectie.py.
    serial.Serial = CityGlowSerialProxy
    cv2.putText = patched_putText

    print("✅ Rulez intersectie.py original, fără modificări.")
    runpy.run_path(str(original_path), run_name="__main__")


if __name__ == "__main__":
    server_thread = threading.Thread(target=start_server_thread, daemon=True)
    server_thread.start()

    time.sleep(0.5)
    run_original_intersectie()
