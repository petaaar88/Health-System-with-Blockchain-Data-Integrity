from backend.network.peer import Peer
import sys
import asyncio


async def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    peer = Peer(port)
    
    initial_peers = []
    if len(sys.argv) > 2:
        
        await peer.load_data_from_peer(f"ws://localhost:{sys.argv[2]}")

        for peer_arg in sys.argv[2:]:
            if peer_arg.isdigit():
                uri = f"ws://localhost:{peer_arg}"
            else:
                uri = peer_arg
            initial_peers.append(uri)
    
    await peer.run(initial_peers)


if __name__ == "__main__":
    asyncio.run(main())