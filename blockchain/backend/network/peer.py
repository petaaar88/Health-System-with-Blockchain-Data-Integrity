import asyncio
import websockets
import json
from datetime import datetime
import uuid
import threading
from blockchain.backend.util import util
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

        # transaction validation consensus
        self.is_transaction_validation = False
        self.transaction_votes = []

        # block validation consensus
        self.block_votes = []
        self.mined_block = None

        # Poboljšano za consensus blokova
        self.block_consensus_lock = asyncio.Lock()  # mutex za thread safety
        self.received_blocks = {}  # {timestamp: block} - čuva sve primljene blokove
        self.consensus_finalized = False  # da li je konsenzus završen
        self.block_processing_timeout = 2.0  # sekunde za čekanje svih blokova

    async def send_message(self, ws, msg_type, data):
        """Šalje poruku preko websocket konekcije"""
        try:
            message = json.dumps({
                "type": msg_type,
                "data": data,
                "sender_id": self.my_id
            })
            await ws.send(message)
        except Exception as e:
            # caller will handle cleanup of disconnected peers
            raise

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

            elif msg_type == "NEW_BLOCK":
                await self._handle_new_block(sender_id, data)

            elif msg_type == "PEERS":
                await self._handle_peers_list(sender_id, data)

            # CLIENT messages
            elif msg_type == "CLIENT_ADD_TRANSACTION":
                await self._handle_add_transaction(data)

            elif msg_type == "CLIENT_GET_CHAIN":
                await self._handle_getting_chain(ws)

            # Transaction messages
            elif msg_type == "VERIFY_TRANSACTION":
                await self._handle_verify_transaction(data)

            elif msg_type == "TRANSACTION_VOTE":
                self._handle_transactin_vote(data)

            # Block messages
            elif msg_type == "VERIFY_BLOCK":
                await self._handle_verify_block(data, sender_id)

            # Novo - finalni blok
            elif msg_type == "FINAL_BLOCK_CONSENSUS":
                await self._handle_final_block_consensus(data)

            else:
                print(f"[WARN] Unknown message type: {msg_type}")

        except Exception as e:
            print(f"[ERROR] handle_message: {e}")

    async def _handle_add_transaction(self, data):
        """Klijent doda transakciju — pokrećemo validation gossip"""
        print(f"🆕 [INFO] Peer {self.my_id}: Handling new transaction from client")
        
        # Postavimo stanje validacije i očistimo prethodne glasove
        self.is_transaction_validation = True
        self.transaction_votes = []

        # Proširimo poruku (gossip) svima
        await self.broadcast("VERIFY_TRANSACTION", data)

        # Lokalna provera i glas
        transaction_vote = {"id": self.my_id, "vote": self.verify_transaction(data)}
        self.transaction_votes.append(transaction_vote)
        await self.broadcast("TRANSACTION_VOTE", transaction_vote)

    def verify_transaction(self, data):
        self.is_transaction_validation = True
        medical_record = data.get("data_for_validation")
        transaction = Transaction.from_dict(data.get("transaction"))

        is_valid = False

        if self.chain.add_transaction(transaction, medical_record):
            print(f"\n✅ [INFO] Peer {self.my_id}: Transaction {transaction.id} is valid.")
            is_valid = True
        else:
            print(f"\n❌ [INFO] Peer {self.my_id}: Transaction {transaction.id} is invalid!")
            is_valid = False

        return is_valid

    async def _handle_verify_transaction(self, data):
        # Kada primimo VERIFY_TRANSACTION, uverimo se da resetujemo stanje ako nije aktivno
        print(f"🔍 [RECV {util.get_current_time_precise()}]  Peer {self.my_id}: Transaction for validation {Transaction.from_dict(data.get("transaction")).id}")

        
        self.is_transaction_validation = True
        self.transaction_votes = []

        transaction_vote = {"id": self.my_id, "vote": self.verify_transaction(data)}
        self.transaction_votes.append(transaction_vote)
        await self.broadcast("TRANSACTION_VOTE", transaction_vote)

    def _handle_transactin_vote(self, data):
        # Dodaj glas ako već nije dodat
        self.transaction_votes.append(data)

    async def _handle_verify_block(self, data, sender_id):
        async with self.block_consensus_lock:
            if self.consensus_finalized:
                print(f"Konsenzus već završen, ignoriše blok od {sender_id}")
                return

            # Zaustavi mining kod svih
            self.chain.can_mine = False
            self.chain.is_mining = False

            print(f"Primljen VERIFY_BLOCK od {sender_id}")
            temp_block = Block.from_dict(data)
            timestamp = temp_block.header.timestamp

            print(f"Blok vreme: {timestamp}, miner: {temp_block.header.miner}")

            # Dodaj primljeni blok u kolekciju
            # Ako već postoji blok sa istim timestamp-om, ignorisemo duplikat
            if timestamp not in self.received_blocks:
                self.received_blocks[timestamp] = {
                    "block": temp_block,
                    "sender": sender_id
                }

            # Dodaj naš blok ako postoji
            if self.chain.mined_block is not None and self.chain.mined_block.header.timestamp not in self.received_blocks:
                our_timestamp = self.chain.mined_block.header.timestamp
                self.received_blocks[our_timestamp] = {
                    "block": self.chain.mined_block,
                    "sender": self.my_id
                }
                print(f"Dodao naš blok: {our_timestamp}")

            # Pokreni timeout za finalizaciju konsenzusa (ako već nije pokrenut)
            # Kreiramo task bez blokiranja da bi svi primili poruke
            asyncio.create_task(self._finalize_consensus_after_timeout())

    async def _finalize_consensus_after_timeout(self):
        """Čeka kratko vreme pa finalizuje konsenzus"""
        await asyncio.sleep(self.block_processing_timeout)

        async with self.block_consensus_lock:
            if self.consensus_finalized:
                return  # već je završeno

            if not self.received_blocks:
                print("Nema primljenih blokova za konsenzus")
                # Resetuj mining stanje ali ostavi transaction handling aktivan
                self.chain.can_mine = True
                self.chain.is_mining = False
                return

            print(f"Finalizujem konsenzus sa {len(self.received_blocks)} blokova")

            # Sortiraj blokove po timestamp-u (najstariji pobjeđuje)
            sorted_timestamps = sorted(self.received_blocks.keys())
            winning_timestamp = sorted_timestamps[0]
            winning_block_info = self.received_blocks[winning_timestamp]
            winning_block = winning_block_info["block"]
            winning_sender = winning_block_info["sender"]

            print(f"Pobednički blok: {winning_timestamp} od {winning_sender}")

            # Postavi finalni blok
            self.mined_block = winning_block
            self.consensus_finalized = True

            # Pošalji finalni konsenzus svim nodovima
            await self.broadcast("FINAL_BLOCK_CONSENSUS", {
                "winning_block": winning_block.to_dict(),
                "winning_sender": winning_sender,
                "total_blocks": len(self.received_blocks),
                "finalizer": self.my_id
            })

            print(f"🎯 KONSENZUS FINALIZOVAN: Blok {winning_timestamp} od {winning_sender}")

            try:
                if Block.is_valid(self.mined_block, self.chain):
                    #TODO odkomentaisi
                    #self.chain.add_to_block_to_chain(self.mined_block)
                    #print(f"✅ Finalni blok dodat u lanac: {winning_timestamp}")
                    print("validan je")
            except Exception as e:
                print(f"[ERROR] Pri dodavanju finalnog bloka u lokalni lanac: {e}")

            # Resetuj SAMO block consensus stanje, ne i transaction validation
            self.reset_block_consensus()
            self.chain.can_mine = True
            self.chain.is_mining = False
            self.chain.mined_block = None

    async def _handle_final_block_consensus(self, data):
        async with self.block_consensus_lock:
            if self.consensus_finalized:
                return  # već je postavljen finalni konsenzus

            winning_block = Block.from_dict(data.get("winning_block"))
            winning_sender = data.get("winning_sender")
            finalizer = data.get("finalizer")
            total_blocks = data.get("total_blocks")

            print(f"🏆 Primljen FINALNI KONSENZUS od {finalizer}:")
            print(f"   Ukupno blokova: {total_blocks}")

            # SVI postavljaju isti finalni blok
            self.mined_block = winning_block
            self.consensus_finalized = True

            # Dodaj finalni blok u lokalni lanac ako je validan
            try:
                if self.chain.get_last_block().header.height != self.mined_block.header.height:
                    if Block.is_valid(self.mined_block, self.chain):
                        self.chain.add_to_block_to_chain(self.mined_block)
                        print(f"✅ Finalni blok dodat u lokalni lanac:")
            except Exception as e:
                print(f"[ERROR] Pri dodavanju finalnog bloka u lokalni lanac: {e}")

            # Resetuj stanje za sledeći mining ciklus
            self.reset_block_consensus()
            self.chain.can_mine = True
            self.chain.is_mining = False
            self.chain.mined_block = None
            self.is_transaction_validation = False
            self.transaction_votes = []

            print(f"✅ SVI NODOVI: Finalni blok postavljen - {self.mined_block.header if self.mined_block else 'none'}")

    async def _handle_mine(self, ws, data):

        medical_record = data.get("data_for_validation")
        transaction = Transaction.from_dict(data.get("transaction"))

        if self.chain.add_transaction(transaction, medical_record) is True:
            new_block = self.chain.create_new_block()

        if Block.is_valid(new_block, self.chain) is True:
            self.chain.add_to_block_to_chain(new_block)

        response = {"chain": []}
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

        response = {"chain": []}
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
        # koristimo ceil-like ponašanje
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
            # Pokreni rudarenje u odvojenom thread-u
            print(f"\n⛏️ [INFO] Peer {self.my_id}: Mining started at {util.get_current_time_precise()}")
            mining_thread = threading.Thread(target=self.chain.create_new_block, daemon=True)
            mining_thread.start()

        else:
            print(f"👥❌ Transaction  REJECTED by consensus")

        self.is_transaction_validation = False
        self.transaction_votes = []

    def reset_block_consensus(self):
        """Resetuje stanje konsenzusa za novi mining ciklus"""
        self.received_blocks.clear()
        self.consensus_finalized = False
        # NE diramo mined_block ovde — mined_block se čuva dok se ne finalizuje i doda u lanac

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
                    try:
                        ws = self.outgoing_peers[uri]
                        await ws.close()
                    except Exception:
                        pass
                    del self.outgoing_peers[uri]

    async def broadcast(self, msg_type, data):
        """Broadcast poruke svim povezanim peer-ovima (samo outgoing da se izbegnu duplikati)"""
        disconnected_peers = []

        # Šalji SAMO preko outgoing konekcija da se izbegnu duplikati
        # Incoming peer će primiti preko svoje outgoing konekcije
        for uri, ws in list(self.outgoing_peers.items()):
            try:
                await self.send_message(ws, msg_type, data)
                print(f"👥 [SENT {util.get_current_time_precise()}] Peer {self.my_id}: {msg_type} to {uri}")
            except Exception as e:
                print(f"[ERROR] Failed to send to {uri}: {e}")
                disconnected_peers.append(uri)

        # Ukloni neispravne konekcije
        for uri in disconnected_peers:
            if uri in self.outgoing_peers:
                del self.outgoing_peers[uri]
                
        print(f"🔍 [BROADCAST] Peer {self.my_id}: Sent {msg_type} to {len(self.outgoing_peers)} outgoing peers \n")


    async def update_loop(self):
        """Loop za korisnikov input i proveru stanja"""
        loop = asyncio.get_event_loop()
        while True:

            # Transaction consensus: pokreni proveru kada imamo koliko glasova koliko znamo u mrezi
            if self.is_transaction_validation and self.get_network_size() == len(self.transaction_votes):
                print("************************** ovde")
                print(self.transaction_votes)
                self._check_transaction_consensus()

            # Kada lokalno miner završi, pošalji VERIFY_BLOCK samo ako postoji mined_block
            if self.chain.is_mining and not self.consensus_finalized:
                if self.chain.mined_block is not None:
                    block_to_send = self.chain.mined_block
                    # stop mining locally
                    self.chain.is_mining = False

                    print(f"🚀 Šaljem blok na konsenzus: {block_to_send.header.timestamp}")
                    print("\n")
                    await self.broadcast("VERIFY_BLOCK", block_to_send.to_dict())

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
