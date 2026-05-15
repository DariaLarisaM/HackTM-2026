import asyncio
import json
import websockets

async def handler(websocket):
    print("🚀 Interfața web s-a conectat la WebSocket!")
    try:
        # Trimitem o stare normală inițială imediat după conectare
        await websocket.send(json.dumps({
            "state": "1",
            "incident": False,
            "objects_b1": 4,
            "objects_b2": 2
        }))

        # Ținem conexiunea deschisă
        async for message in websocket:
            pass
    except websockets.exceptions.ConnectionClosedOK:
        print("🔌 Interfața s-a deconectat.")

async def main():
    async with websockets.serve(handler, "localhost", 8765):
        print("✅ Serverul de WebSockets rulează live pe ws://localhost:8765")
        await asyncio.Future() # Rămâne pornit la nesfârșit

if __name__ == "__main__":
    asyncio.run(main())