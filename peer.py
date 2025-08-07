import asyncio
import websockets
import json
import sys

peers = set()
known_peer_uris = set()

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
MY_URI = f"ws://localhost:{PORT}"

# ------------------------------------

async def send_message(ws, msg_type, data):
    message = json.dumps({
        "type": msg_type,
        "data": data
    })
    await ws.send(message)

async def handle_message(ws, message):
    try:
        msg = json.loads(message)
        msg_type = msg.get("type")
        data = msg.get("data")

        if msg_type == "PING":
            print(f"[RECV] PING")
            await send_message(ws, "PONG", {})
        elif msg_type == "PONG":
            print(f"[RECV] PONG")
        elif msg_type == "NEW_BLOCK":
            print(f"[RECV] NEW_BLOCK: {data}")
        elif msg_type == "PEERS":
            print(f"[RECV] PEERS list: {data}")
            for uri in data:
                if uri != MY_URI and uri not in known_peer_uris:
                    known_peer_uris.add(uri)
                    asyncio.create_task(connect_to_peer(uri))
        else:
            print(f"[WARN] Unknown message type: {msg_type}")

    except Exception as e:
        print(f"[ERROR] handle_message: {e}")

# ------------------------------------

async def peer_server():
    async def handler(ws):
        peers.add(ws)
        print("[INFO] New peer connected.")
        try:
            await send_message(ws, "PEERS", list(known_peer_uris))  # pošalji mu sve koje znamo
            async for message in ws:
                await handle_message(ws, message)
        finally:
            peers.remove(ws)
            print("[INFO] Peer disconnected.")

    return await websockets.serve(handler, "localhost", PORT)

# ------------------------------------

async def connect_to_peer(uri):
    while True:
        try:
            if uri == MY_URI:
                return
            ws = await websockets.connect(uri)
            if ws in peers:
                return
            peers.add(ws)
            known_peer_uris.add(uri)
            print(f"[INFO] Connected to peer {uri}")

            await send_message(ws, "PING", {})
            await send_message(ws, "PEERS", list(known_peer_uris))
            await send_message(ws, "NEW_BLOCK", {"block": f"Genesis from {PORT}"})

            async for message in ws:
                await handle_message(ws, message)

        except Exception as e:
            print(f"[WARN] Could not connect to {uri}, retrying in 5s: {e}")
            await asyncio.sleep(5)

# ------------------------------------

async def broadcast(msg_type, data):
    for ws in peers.copy():
        try:
            await send_message(ws, msg_type, data)
        except:
            peers.remove(ws)

# ------------------------------------

async def user_input_loop():
    loop = asyncio.get_event_loop()
    while True:
        await loop.run_in_executor(None, input, "[You] Press ENTER to broadcast NEW_BLOCK\n")
        await broadcast("NEW_BLOCK", {"block": f"Manual block from {PORT}"})


async def main():
    await peer_server()
    print(f"[INFO] P2P server listening on port {PORT}")

    # Poveži se na peerove poznate pri pokretanju
    if len(sys.argv) > 2:
        for peer_arg in sys.argv[2:]:
            if peer_arg.isdigit():
                uri = f"ws://localhost:{peer_arg}"
            else:
                uri = peer_arg  # ako neko ipak stavi ceo URI

            if uri != MY_URI:
                known_peer_uris.add(uri)
                asyncio.create_task(connect_to_peer(uri))


    asyncio.create_task(user_input_loop())

    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
