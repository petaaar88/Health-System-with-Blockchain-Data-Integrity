import asyncio
import websockets
import json
import sys
import uuid


# Razdvojimo incoming i outgoing konekcije
incoming_peers = {}    # {ws: peer_info}
outgoing_peers = {}    # konekcije koje smo mi napravili ka drugima {uri: ws}
known_peers = {}       # {peer_id: {"uri": uri, "id": peer_id}}
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
MY_URI = f"ws://localhost:{PORT}"
MY_ID = str(uuid.uuid4())[:8]  # Kratki jedinstveni ID

# ------------------------------------

async def send_message(ws, msg_type, data):
    message = json.dumps({
        "type": msg_type,
        "data": data,
        "sender_id": MY_ID
    })
    await ws.send(message)

async def handle_message(ws, message):
    try:
        msg = json.loads(message)
        msg_type = msg.get("type")
        data = msg.get("data")
        sender_id = msg.get("sender_id", "unknown")

        if msg_type == "HANDSHAKE":
            peer_id = data.get("peer_id")
            peer_uri = data.get("uri")
            print(f"🤝 [RECV] Peer {MY_ID}: HANDSHAKE from {peer_id} ({peer_uri})")
            
            # Dodaj peer u incoming_peers sa njegovim ID-om
            incoming_peers[ws] = {"id": peer_id, "uri": peer_uri}
            known_peers[peer_id] = {"uri": peer_uri, "id": peer_id}
            
            # Odgovori sa svojim handshake
            await send_message(ws, "HANDSHAKE_ACK", {
                "peer_id": MY_ID,
                "uri": MY_URI
            })
            
        elif msg_type == "HANDSHAKE_ACK":
            peer_id = data.get("peer_id")
            peer_uri = data.get("uri")
            print(f"🤝 [RECV] Peer {MY_ID}: HANDSHAKE_ACK from {peer_id} ({peer_uri})")
            known_peers[peer_id] = {"uri": peer_uri, "id": peer_id}
            
        elif msg_type == "PING":
            print(f"📶 [RECV] Peer {MY_ID}: PING from {sender_id}")
            await send_message(ws, "PONG", {})
        elif msg_type == "PONG":
            print(f"✅ [RECV] Peer {MY_ID}: PONG from {sender_id}")
        elif msg_type == "NEW_BLOCK":
            print(f"[RECV] NEW_BLOCK from {sender_id}: {data}")
        elif msg_type == "PEERS":
            print(f"📋 [RECV] Peer {MY_ID}: PEERS list from {sender_id}: {data}\n")
            for peer_info in data:
                peer_uri = peer_info.get("uri")
                peer_id = peer_info.get("id")
                if peer_uri != MY_URI and peer_uri not in outgoing_peers and peer_id != MY_ID:
                    asyncio.create_task(connect_to_peer(peer_uri))
        else:
            print(f"[WARN] Unknown message type: {msg_type}")

    except Exception as e:
        print(f"[ERROR] handle_message: {e}")

# ------------------------------------

async def start_peer_server():
    async def handler(ws):
        #print(f"Peer {MY_ID} na portu {PORT}. Nova konekcija: {ws}")
        try:
            async for message in ws:
                await handle_message(ws, message)
        finally:
            # Ukloni peer iz incoming_peers
            if ws in incoming_peers:
                peer_info = incoming_peers[ws]
                print(f"[INFO] Incoming peer {peer_info['id']} disconnected.")
                del incoming_peers[ws]

    return await websockets.serve(handler, "localhost", PORT)

# ------------------------------------

async def connect_to_peer(uri):
    if uri == MY_URI or uri in outgoing_peers:
        return
        
    retry_count = 0
    max_retries = 3
    
    while retry_count < max_retries:
        try:
            print(f"🔄 [INFO] Peer {MY_ID}: Trying to connect to {uri} (attemps {retry_count + 1})")
            ws = await websockets.connect(uri)
            outgoing_peers[uri] = ws
            print(f"🔗 [INFO] Peer {MY_ID}: Connected to {uri}")

            # Pošaljemo handshake sa našim ID-om
            await send_message(ws, "HANDSHAKE", {
                "peer_id": MY_ID,
                "uri": MY_URI
            })
            
            await send_message(ws, "PING", {})
            
            # Pošaljemo listu svih peerova koje znamo
            peer_list = [{"uri": info["uri"], "id": info["id"]} for info in known_peers.values()]
            peer_list.append({"uri": MY_URI, "id": MY_ID})  # dodaj sebe
            await send_message(ws, "PEERS", peer_list)
            
            await send_message(ws, "NEW_BLOCK", {"block": f"Genesis from {MY_ID}"})

            async for message in ws:
                await handle_message(ws, message)

        except Exception as e:
            print(f"[WARN] {MY_ID} ne može da se poveže na {uri}: {e}")
            retry_count += 1
            if retry_count < max_retries:
                await asyncio.sleep(2)
            else:
                print(f"[ERROR] {MY_ID} nije uspeo da se poveže na {uri} nakon {max_retries} pokušaja")
                break
        finally:
            # Cleanup
            if uri in outgoing_peers:
                del outgoing_peers[uri]

# ------------------------------------

async def broadcast(msg_type, data):
    # Broadcast samo preko outgoing konekcija da izbegnemo duplikate
    disconnected_peers = []
    
    for uri, ws in outgoing_peers.copy().items():
        try:
            await send_message(ws, msg_type, data)
            print(f"[SENT] {msg_type} from {MY_ID} to {uri}")
        except Exception as e:
            print(f"[ERROR] Failed to send to {uri}: {e}")
            disconnected_peers.append(uri)
    
    # Ukloni neispravne konekcije
    for uri in disconnected_peers:
        if uri in outgoing_peers:
            del outgoing_peers[uri]

# ------------------------------------

async def user_input_loop():
    loop = asyncio.get_event_loop()
    while True:
        await loop.run_in_executor(None, input, f"[Peer {MY_ID}] Press ENTER to broadcast NEW_BLOCK. Connected peers: {list(outgoing_peers.keys())}\n")
        await broadcast("NEW_BLOCK", {"block": f"Manual block from {MY_ID}"})

async def main():
    await start_peer_server()
    print(f"🚀 PEER {MY_ID} started on {MY_URI}\n")

    # Poveži se na peerove poznate pri pokretanju
    if len(sys.argv) > 2:
        for peer_arg in sys.argv[2:]:
            if peer_arg.isdigit():
                uri = f"ws://localhost:{peer_arg}"
            else:
                uri = peer_arg

            if uri != MY_URI:
                asyncio.create_task(connect_to_peer(uri))

    asyncio.create_task(user_input_loop())

    while True:
        await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())