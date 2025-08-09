import asyncio
import websockets
import json
import uuid
import threading
from blockchain.backend.core.chain import Chain
from blockchain.backend.core.transaction import Transaction
from blockchain.backend.core.block import Block

class Peer:
    def __init__(self, port=8765):
        self.port = port
        self.my_uri = f"ws://localhost:{port}"
        self.my_id = str(uuid.uuid4())[:8]
        self.chain = Chain(self.my_id)
        
        # Razdvojimo incoming i outgoing konekcije
        self.incoming_peers = {}    # {ws: peer_info}
        self.outgoing_peers = {}    # konekcije koje smo mi napravili ka drugima {uri: ws}
        self.known_peers = {}       # {peer_id: {"uri": uri, "id": peer_id}}

        self.consensus_threshold = 0.51  # 51% konsenzus


        #transaction validatoin concensus
        self.is_transaction_validation = False
        self.transaction_votes = []
    
    async def send_message(self, ws, msg_type, data):
        """Šalje poruku preko websocket konekcije"""
        message = json.dumps({
            "type": msg_type,
            "data": data,
            "sender_id": self.my_id
        })
        await ws.send(message)
    
    async def handle_message(self, ws, message):
        """Obrađuje primljene poruke"""
        try:
            msg = json.loads(message)
            msg_type = msg.get("type")
            data = msg.get("data")
            sender_id = msg.get("sender_id", "unknown")

            if msg_type == "HANDSHAKE":
                await self._handle_handshake(ws, data)
                
            elif msg_type == "HANDSHAKE_ACK":
                await self._handle_handshake_ack(data)
                #TODO obrisi ovo
            elif msg_type == "NEW_BLOCK":
                await self._handle_new_block(sender_id, data)
                
            elif msg_type == "PEERS":
                await self._handle_peers_list(sender_id, data)

            #CLIENT messages    
                
            elif msg_type == "CLIENT_ADD_TRANSACTION":
                await self._handle_add_transaction(data)

            #TODO prepavi da drugacije radi, da mora da postoji verifikacija svih nodova pre nego sto se posalje
            elif msg_type == "CLIENT_GET_CHAIN":
                await self._handle_getting_chain(ws)

            # Transaction messages
            elif msg_type == "VERIFY_TRANSACTION":
                await self._handle_verify_transaction(data)

            elif msg_type == "TRANSACTION_VOTE":
                await self._handle_transactin_vote(data)

            #TODO obrisi jer je samo pokazna metoda koja pokazuje kako radi blockchain kada mu se sa strane posalju podaci
            elif msg_type == "MINE":
                await self._handle_mine(ws, data)

            else:
                print(f"[WARN] Unknown message type: {msg_type}")

        except Exception as e:
            print(f"[ERROR] handle_message: {e}")
    
    async def _handle_add_transaction(self,data):

        await self.broadcast("VERIFY_TRANSACTION", data)
        transaction_vote = {"id":self.my_id, "vote":self.verify_transaction(data)}

        self.transaction_votes.append(transaction_vote)
        await self.broadcast("TRANSACTION_VOTE",transaction_vote)
       

    def verify_transaction(self,data):
        self.is_transaction_validation = True
        medical_record = data["data_for_validation"]
        
        transaction = Transaction.from_dict(data["transaction"])

        is_valid = False

        if self.chain.add_transaction(transaction,medical_record):
            print(f"\n✅ [INFO] Peer {self.my_id}: Transaction {transaction.id} is valid.")
            is_valid = True
        else:
            print(f"\n❌ [INFO] Peer {self.my_id}: Transaction {transaction.id} is invalid!")
            is_valid = False
        
        return is_valid

    async def _handle_verify_transaction(self, data):
        
        transaction_vote = {"id":self.my_id, "vote":self.verify_transaction(data)}

        self.transaction_votes.append(transaction_vote)
        await self.broadcast("TRANSACTION_VOTE",transaction_vote)

    async def _handle_transactin_vote(self,data):
        self.transaction_votes.append(data)

    #TODO obrisi jer je samo pokazna metoda koja pokazuje kako radi blockchain kada mu se sa strane posalju podaci
    async def _handle_mine(self,ws, data):

        medical_record = data["data_for_validation"]
        transaction = Transaction.from_dict(data["transaction"])

        if self.chain.add_transaction(transaction,medical_record) is True:
            new_block = self.chain.create_new_block()
        
        if Block.is_valid(new_block,self.chain) is True:
            self.chain.add_to_block_to_chain(new_block)

        response = {
            "chain":[]
        }
        #TODO neki koncencus imzedj svih nodova da li imaju svi isti chain
        for block in self.chain.chain:
            response["chain"].append(block.to_dict())

        await ws.send(json.dumps(response, indent=4))

    async def _handle_handshake(self, ws, data):
        """Obrađuje HANDSHAKE poruke"""
        peer_id = data.get("peer_id")
        peer_uri = data.get("uri")
        print(f"🤝 [RECV] Peer {self.my_id}: HANDSHAKE from {peer_id} ({peer_uri})")
        
        # Dodaj peer u incoming_peers sa njegovim ID-om
        self.incoming_peers[ws] = {"id": peer_id, "uri": peer_uri}
        self.known_peers[peer_id] = {"uri": peer_uri, "id": peer_id}
        
        # Odgovori sa svojim handshake
        await self.send_message(ws, "HANDSHAKE_ACK", {
            "peer_id": self.my_id,
            "uri": self.my_uri
        })
    
    async def _handle_getting_chain(self, ws):

        response = {
            "chain":[]
        }
        #TODO neki koncencus imzedj svih nodova da li imaju svi isti chain
        for block in self.chain.chain:
            response["chain"].append(block.to_dict())

        await ws.send(json.dumps(response, indent=4))

    async def _handle_handshake_ack(self, data):
        """Obrađuje HANDSHAKE_ACK poruke"""
        peer_id = data.get("peer_id")
        peer_uri = data.get("uri")
        print(f"🤝 [RECV] Peer {self.my_id}: HANDSHAKE_ACK from {peer_id} ({peer_uri})")
        self.known_peers[peer_id] = {"uri": peer_uri, "id": peer_id}

    async def _handle_new_block(self, sender_id, data):
        """Obrađuje NEW_BLOCK poruke"""
        print(f"[RECV] NEW_BLOCK from {sender_id}: {data}")
    
    async def _handle_peers_list(self, sender_id, data):
        """Obrađuje PEERS listu"""
        print(f"📋 [RECV] Peer {self.my_id}: PEERS list from {sender_id}: {data}\n")
        for peer_info in data:
            peer_uri = peer_info.get("uri")
            peer_id = peer_info.get("id")
            if (peer_uri != self.my_uri and 
                peer_uri not in self.outgoing_peers and 
                peer_id != self.my_id):
                asyncio.create_task(self.connect_to_peer(peer_uri))
    
    def get_network_size(self):
        """Vraća broj aktivnih peer-ova u mreži"""
        return len(self.known_peers) + 1  # +1 for self
    
    def calculate_required_votes(self):
        """Izračunava potreban broj glasova za konsenzus"""
        network_size = self.get_network_size()
        return int(network_size * self.consensus_threshold) + 1

    def _check_transaction_consensus(self):
        
        required_votes = self.calculate_required_votes()

        print("Potrebni glasovi" + str(required_votes))
        
        def izdvoji_po_validnosti(lista):
            validne = [item for item in lista if item.get("vote") is True]
            nevalidne = [item for item in lista if item.get("vote") is False]
            return validne, nevalidne
        
        positive_votes, negative_votes = izdvoji_po_validnosti(self.transaction_votes)
        
        if len(positive_votes) >= required_votes:
            print(f"👥✅ Transaction  ACCEPTED by consensus")
            mining_thread = threading.Thread(target=self.chain.create_new_block, daemon=True)
            mining_thread.start()
            
        else:
            print(f"👥❌ Transaction  REJECTED by consensus")
        
        self.is_transaction_validation = False
    

    async def start_server(self):
        """Pokretanje peer servera"""
        async def handler(ws):
            try:
                async for message in ws:
                    await self.handle_message(ws, message)
            finally:
                # Ukloni peer iz incoming_peers
                if ws in self.incoming_peers:
                    peer_info = self.incoming_peers[ws]
                    print(f"[INFO] Incoming peer {peer_info['id']} disconnected.")
                    del self.incoming_peers[ws]

        return await websockets.serve(handler, "localhost", self.port)
    
    async def connect_to_peer(self, uri):
        """Povezivanje sa drugim peer-om"""
        if uri == self.my_uri or uri in self.outgoing_peers:
            return
            
        retry_count = 0
        max_retries = 3
        
        while retry_count < max_retries:
            try:
                print(f"🔄 [INFO] Peer {self.my_id}: Trying to connect to {uri} (attempt {retry_count + 1})")
                ws = await websockets.connect(uri)
                self.outgoing_peers[uri] = ws
                print(f"🔗 [INFO] Peer {self.my_id}: Connected to {uri}")

                # Pošaljemo handshake sa našim ID-om
                await self.send_message(ws, "HANDSHAKE", {
                    "peer_id": self.my_id,
                    "uri": self.my_uri
                })
                
                await self.send_message(ws, "PING", {})
                
                # Pošaljemo listu svih peerova koje znamo
                peer_list = [{"uri": info["uri"], "id": info["id"]} for info in self.known_peers.values()]
                peer_list.append({"uri": self.my_uri, "id": self.my_id})  # dodaj sebe
                await self.send_message(ws, "PEERS", peer_list)
                
                async for message in ws:
                    await self.handle_message(ws, message)

            except Exception as e:
                print(f"[WARN] {self.my_id} ne može da se poveže na {uri}: {e}")
                retry_count += 1
                if retry_count < max_retries:
                    await asyncio.sleep(2)
                else:
                    print(f"[ERROR] {self.my_id} nije uspeo da se poveže na {uri} nakon {max_retries} pokušaja")
                    break
            finally:
                # Cleanup
                if uri in self.outgoing_peers:
                    del self.outgoing_peers[uri]
    
    async def broadcast(self, msg_type, data):
        """Broadcast poruke svim povezanim peer-ovima"""
        # Broadcast samo preko outgoing konekcija da izbegnemo duplikate
        disconnected_peers = []
        
        for uri, ws in self.outgoing_peers.copy().items():
            try:
                await self.send_message(ws, msg_type, data)
                print(f"👥 [SENT] Peer {self.my_id}: {msg_type} from {self.my_id} to {uri}")
            except Exception as e:
                print(f"[ERROR] Failed to send to {uri}: {e}")
                disconnected_peers.append(uri)
        
        # Ukloni neispravne konekcije
        for uri in disconnected_peers:
            if uri in self.outgoing_peers:
                del self.outgoing_peers[uri]
    
    async def update_loop(self):
        """Loop za korisnikov input"""
        loop = asyncio.get_event_loop()
        while True:
            if self.is_transaction_validation and self.get_network_size() == len(self.transaction_votes):
                self._check_transaction_consensus()
                

            await asyncio.sleep(0.1)  # mala pauza da se event loop oslobodi
    
    async def run(self, initial_peers=None):
        """Glavna metoda za pokretanje peer-a"""
        await self.start_server()
        print(f"🚀 PEER {self.my_id} started on {self.my_uri}\n")

        # Poveži se na početne peer-ove
        if initial_peers:
            for peer_uri in initial_peers:
                if peer_uri != self.my_uri:
                    asyncio.create_task(self.connect_to_peer(peer_uri))

        # Pokreni user input loop
        asyncio.create_task(self.update_loop())

        # Beskonačan loop
        while True:
            await asyncio.sleep(5)


