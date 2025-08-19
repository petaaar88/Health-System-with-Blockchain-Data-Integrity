import asyncio
import websockets
import json
from datetime import datetime
import uuid
import threading
from collections import deque
from backend.util import util
from backend.core.chain import Chain
from backend.core.transaction import Transaction
from backend.core.block import Block
from backend.core.account import Account

class Peer:
    def __init__(self, port=8765):
        self.port = port
        self.my_uri = f"ws://localhost:{port}"
        self.my_id = str(uuid.uuid4())[:8]
        self.chain = Chain(self.my_id)
        self.chain.load_chain_from_file(port)
        self.chain.port = self.port
        self.chain.chech_accounts_db(self.port)

        self.incoming_peers = {}    # {ws: peer_info}
        self.outgoing_peers = {}    # {uri: ws}
        self.known_peers = {}       # {peer_id: {"uri": uri, "id": peer_id}}

        self.consensus_threshold = 0.51  # 51% konsenzus

        # pending transactions mechanism
        self.pending_transactions = deque()  # Queue of pending transactions
        self.current_transaction = None      # Currently processing transaction
        self.is_processing_transaction = False  # Flag to track if we are processing
        self.pending_lock = asyncio.Lock()   # Thread safety for pending queue

        # transaction validation consensus
        self.is_transaction_validation = False
        self.transaction_votes = []

        # block validation consensus
        self.block_votes = []
        self.mined_block = None
        self.block_consensus_lock = asyncio.Lock()  
        self.received_blocks = {}  # {timestamp: block} 
        self.consensus_finalized = False  
        self.block_processing_timeout = 2.0  # waiting for other blocks

        self.client_transactions = {}

    async def add_pending_transaction(self, transaction_data, client_ws=None):
        
        print(f"📋 [CLNT {util.get_current_time_precise()}] Peer {self.my_id}: Add new transaction.")
        
        if client_ws:
            transaction_id = Transaction.from_dict(transaction_data.get("transaction")).id
            self.client_transactions[transaction_id] = client_ws
            print(f"💾 [CLNT {util.get_current_time_precise()}] Peer {self.my_id}: Saved client connection for transaction {transaction_id}")
        
        async with self.pending_lock:
            if not self.is_processing_transaction:
                self.current_transaction = transaction_data
                self.is_processing_transaction = True
                print(f"⚡ [IMMEDIATE {util.get_current_time_precise()}] Peer {self.my_id}: Processing transaction immediately")
                
                await self._handle_add_transaction(transaction_data)
            else:
                self.pending_transactions.append(transaction_data)
                print(f"📝 [QUEUE {util.get_current_time_precise()}] Peer {self.my_id}: Added transaction to pending queue. Queue size: {len(self.pending_transactions)}")

    async def process_next_transaction(self):
        
        async with self.pending_lock:
            if not self.pending_transactions:
                return
            
            
            self.current_transaction = self.pending_transactions.popleft()
            self.is_processing_transaction = True
            
        print(f"⚡ [PROCESSING {util.get_current_time_precise()}] Peer {self.my_id}: Started processing next transaction from queue. Remaining: {len(self.pending_transactions)}")
        
        
        await self._handle_add_transaction(self.current_transaction)

    async def transaction_completed(self):
        
        async with self.pending_lock:
            self.current_transaction = None
            self.is_processing_transaction = False
            
        print(f"✅ [COMPLETED {util.get_current_time_precise()}] Peer {self.my_id}: Transaction processing completed.")
        
        # reset mining state
        self.chain.can_mine = True
        self.chain.is_mining = False
        self.consensus_finalized = False
        self.received_blocks.clear()
        
        
        if self.pending_transactions:
            print(f"🔄 [QUEUE {util.get_current_time_precise()}] Peer {self.my_id}: Processing next transaction from queue")
            await self.process_next_transaction()

    def get_pending_queue_status(self):
        
        return {
            "queue_size": len(self.pending_transactions),
            "is_processing": self.is_processing_transaction,
            "current_transaction_id": Transaction.from_dict(self.current_transaction.get("transaction")).id if self.current_transaction else None
        }

    async def send_message(self, ws, msg_type, data):
        
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
       
        try:
            msg = json.loads(message)
            msg_type = msg.get("type")
            data = msg.get("data")
            sender_id = msg.get("sender_id", "unknown")

            match (msg_type):
                case "HANDSHAKE":
                    await self._handle_handshake(ws, data)
                case "HANDSHAKE_ACK":
                    await self._handle_handshake_ack(data)
                case "PEERS":
                    await self._handle_peers_list(sender_id, data)
                case "GET_DATA":
                    await self._handle_get_data(ws)
                case "RECEIVE_DATA":
                    await self._handle_receive_data(data)
                case "ADD_ACCOUNT":
                    await self._handle_add_account(data)

                # CLIENT messages
                case "CLIENT_ADD_ACCOUNT":
                    await self._handle_client_add_account(ws,data)
                case "CLIENT_ADD_TRANSACTION":
                    await self.add_pending_transaction(data, ws)
                case "CLIENT_GET_CHAIN":
                    await self._handle_client_get_chain(ws)
                case "CLIENT_GET_QUEUE_STATUS":
                    await self._handle_get_queue_status(ws)
                case "CLIENT_VERIFY_TRANSACTION":
                    await self._handle_client_verify_transaction(ws, data)
                case "CLIENT_GET_ALL_TRANSACTIONS_OF_PATIENT":
                    await self._handle_client_get_all_transactions_of_patient(ws, data)

                # Transaction messages
                case "VERIFY_TRANSACTION":
                    await self._handle_verify_transaction(data)
                case "TRANSACTION_VOTE":
                    self._handle_transactin_vote(data)

                # Block messages
                case "VERIFY_BLOCK":
                    await self._handle_verify_block(data, sender_id)
                case "FINAL_BLOCK_CONSENSUS":
                    await self._handle_final_block_consensus(data)

                case _:
                    print(f"⚠️ [WARN {util.get_current_time_precise()}] Peer {self.my_id}: Unknown message type: {msg_type}")

        except Exception as e:
            print(f"⛔ [ERROR {util.get_current_time_precise()}] Peer {self.my_id}: handle_message: {e}")

    async def _handle_client_get_all_transactions_of_patient(self,ws,data):

        print(f"📋 [CLNT {util.get_current_time_precise()}] Peer {self.my_id}: Get all transactions of patient.")

        accounts = util.read_from_json_file(f"./blockchain/db/{str(self.port)}_accounts.json")

        if not any(acc["public_key"]== data for acc in accounts):
            print(f"✅ [INFO {util.get_current_time_precise()}] Peer {self.my_id}: Get all transactions of patient complited.")
            return await ws.send(json.dumps({"message": "Account does not exist!"}))
        
        print(f"✅ [INFO {util.get_current_time_precise()}] Peer {self.my_id}: Get all transactions of patient complited.")
        return await ws.send(json.dumps({"message":self.chain.find_all_transactions_with_public_key(data)}))

    async def _handle_client_verify_transaction(self,ws, data):
        print(f"📋 [CLNT {util.get_current_time_precise()}] Peer {self.my_id}: Verify transaction.")

        health_record_hash = self.chain.find_health_record(data["health_record_id"])
        if health_record_hash == None:
            print(f"✅ [INFO {util.get_current_time_precise()}] Peer {self.my_id}: Verification complited.")
            return await ws.send(json.dumps({"message":"Health record does not exist!"}))

        if util.hash256(data["health_record"]) == health_record_hash:
            print(f"✅ [INFO {util.get_current_time_precise()}] Peer {self.my_id}: Verification complited.")
            return await ws.send(json.dumps({"message":"Health record is valid!"}))
        else:
            print(f"✅ [INFO {util.get_current_time_precise()}] Peer {self.my_id}: Verification complited.")
            return await ws.send(json.dumps({"message":"Health record is invalid!"}))


    async def _handle_client_add_account(self,ws, data):
        print(f"📋 [CLNT {util.get_current_time_precise()}] Peer {self.my_id}: Add account.")
        new_account = {
            "public_key": data["public_key"],
            "private_key": data["private_key"]  
        }
        Account._add_new_account_to_db(new_account,self.port)
        print(f"✅ [INFO {util.get_current_time_precise()}] Peer {self.my_id}: Account added.")
        await ws.send(json.dumps({"message":"Account added!"}))
        await self.broadcast("ADD_ACCOUNT",new_account)
    
    async def _handle_add_account(self, data):
        print(f"📋 [RECV {util.get_current_time_precise()}] Peer {self.my_id}: Add account")
        Account._add_new_account_to_db(data,self.port)
        print(f"✅ [INFO {util.get_current_time_precise()}] Peer {self.my_id}: Account added.")

    async def notify_client_transaction_result(self, transaction_id, success, message):
       
        if transaction_id in self.client_transactions:
            client_ws = self.client_transactions[transaction_id]
            try:
                response = {
                    "type": "TRANSACTION_RESULT",
                    "transaction_id": transaction_id,
                    "success": success,
                    "message": message,
                    "timestamp": util.get_current_time_precise()
                }
                await client_ws.send(json.dumps(response))
                print(f"📤 [CLNT {util.get_current_time_precise()}] Peer {self.my_id}: Sent result to client for transaction {transaction_id}: {message}")
            except Exception as e:
                print(f"⛔ [ERROR {util.get_current_time_precise()}] Failed to notify client for transaction {transaction_id}: {e}")
            finally:
                
                del self.client_transactions[transaction_id]

    async def load_data_from_peer(self, uri):
        print(f"✉️ [INFO {util.get_current_time_precise()}] Peer {self.my_id}: Requesting data from {uri}")

        ws = await websockets.connect(uri)
        try:
            
            await self.send_message(ws, "GET_DATA", {})
            
            
            while True:
                message = await ws.recv()
                data = json.loads(message)  
                
                msg_type = data.get("type")
                msg_data = data.get("data", {})
                
                if msg_type == "RECEIVE_DATA":
                    await self._handle_receive_data(msg_data)
                    break  
                    
        except Exception as e:
            print(f"❌ [INFO] Peer {self.my_id}: Greška pri učitavanju chain-a: {e}")
        finally:
            await ws.close()

    async def _handle_get_data(self, ws):
        print(f"📩 [RECV {util.get_current_time_precise()}] Peer {self.my_id}: Sending data to new peer.")
        accounts = util.read_from_json_file(f"./blockchain/db/{self.port}_accounts.json")
        await self.send_message(ws, "RECEIVE_DATA",{"chain":self.chain.chain_to_dict(),"accounts":accounts})

    async def _handle_receive_data(self, data):
        print(f"🔄 [RECV {util.get_current_time_precise()}] Peer {self.my_id}: Loading data from peer.")
        chain_dict = data["chain"]
        self.chain.chain_from_dict(chain_dict)
        util.write_to_json_file(f"./blockchain/db/{self.port}_accounts.json",data["accounts"])
       

    async def _handle_get_queue_status(self, ws):
       
        status = self.get_pending_queue_status()
        await ws.send(json.dumps(status, indent=2))

    async def _handle_add_transaction(self, data):
       
        print(f"🆕 [INFO {util.get_current_time_precise()}] Peer {self.my_id}: Handling new transaction from client.")
        
        self.is_transaction_validation = True
        self.transaction_votes = []

        
        await self.broadcast("VERIFY_TRANSACTION", data)

        # local validation and vote
        transaction_vote = {"id": self.my_id, "vote": self.verify_transaction(data)}
        self.transaction_votes.append(transaction_vote)
        await self.broadcast("TRANSACTION_VOTE", transaction_vote)

    def verify_transaction(self, data):
        self.is_transaction_validation = True
        health_record = data.get("data_for_validation")
        transaction = Transaction.from_dict(data.get("transaction"))

        is_valid = False
        
        if self.chain.add_transaction(transaction, health_record):
            print(f"\n✅ [INFO {util.get_current_time_precise()}] Peer {self.my_id}: Transaction {transaction.id} is valid.")
            is_valid = True
        else:
            print(f"\n❌ [INFO {util.get_current_time_precise()}] Peer {self.my_id}: Transaction {transaction.id} is invalid!")
            is_valid = False

        return is_valid

    async def _handle_verify_transaction(self, data):
        
        print(f"🔍 [RECV {util.get_current_time_precise()}]  Peer {self.my_id}: Transaction for validation {Transaction.from_dict(data.get('transaction')).id}")

        
        self.is_transaction_validation = True
        self.transaction_votes = []

        transaction_vote = {"id": self.my_id, "vote": self.verify_transaction(data)}
        self.transaction_votes.append(transaction_vote)
        await self.broadcast("TRANSACTION_VOTE", transaction_vote)

    def _handle_transactin_vote(self, data):
        self.transaction_votes.append(data)

    async def _handle_verify_block(self, data, sender_id):
        async with self.block_consensus_lock:
            if self.consensus_finalized:
                print(f"  [INFO {util.get_current_time_precise()}] Peer {self.my_id}: Consensus over, ignore block from {sender_id}")
                return

            # Stop mining on all peers
            self.chain.can_mine = False
            self.chain.is_mining = False

            print(f"📩 [RECV {util.get_current_time_precise()}] Peer {self.my_id}: Recived block for validation from {sender_id} peer.")
            temp_block = Block.from_dict(data)
            timestamp = temp_block.header.timestamp

            print(f"📦 [INFO {util.get_current_time_precise()}] Peer {self.my_id}: Peer {temp_block.header.miner} mined block at {timestamp}.")

            # add recived block to collection
            # if block with same timestamp exitst in collection, ignore duplicate
            if timestamp not in self.received_blocks:
                self.received_blocks[timestamp] = {
                    "block": temp_block,
                    "sender": sender_id
                }

            
            if self.chain.mined_block is not None and self.chain.mined_block.header.timestamp not in self.received_blocks:
                our_timestamp = self.chain.mined_block.header.timestamp
                self.received_blocks[our_timestamp] = {
                    "block": self.chain.mined_block,
                    "sender": self.my_id
                }
                print(f"📦 [INFO {util.get_current_time_precise()}] Peer {self.my_id}: Added our block mined at {our_timestamp}.")

            asyncio.create_task(self._finalize_consensus_after_timeout())

    async def _finalize_consensus_after_timeout(self):
        
        await asyncio.sleep(self.block_processing_timeout)

        async with self.block_consensus_lock:
            if self.consensus_finalized:
                return  
            if not self.received_blocks:
                print(f"  [INFO {util.get_current_time_precise()}] Peer {self.my_id}: No blocks for consensus.")
                
                self.chain.can_mine = True
                self.chain.is_mining = False
                return

            print(f"🔚 [INFO {util.get_current_time_precise()}] Peer {self.my_id}: Finalizing consensus with {len(self.received_blocks)} blocks.")

            # sort blocks by timestamp (oldest wins)
            sorted_timestamps = sorted(self.received_blocks.keys())
            winning_timestamp = sorted_timestamps[0]
            winning_block_info = self.received_blocks[winning_timestamp]
            winning_block = winning_block_info["block"]
            winning_sender = winning_block_info["sender"]

            print(f"🏆 [INFO {util.get_current_time_precise()}] Peer {self.my_id}: WINNER block mined at {winning_timestamp} by {winning_sender} peer.")

            # set final block
            self.mined_block = winning_block
            self.consensus_finalized = True

            # send final concensus to all peers
            await self.broadcast("FINAL_BLOCK_CONSENSUS", {
                "winning_block": winning_block.to_dict(),
                "winning_sender": winning_sender,
                "total_blocks": len(self.received_blocks),
                "finalizer": self.my_id
            })

            print(f"🎯 [INFO {util.get_current_time_precise()}] Peer {self.my_id}:  Consensus finalized. Blok mined at {winning_timestamp} by {winning_sender}")

            try:
                if Block.is_valid(self.mined_block, self.chain):
                    
                    # NOVO: Završi transakciju samo ako je ovo node koji je kopao blok
                    if winning_sender == self.my_id and self.is_processing_transaction:
                        print(f"🎯 [MINE SUCCESS {util.get_current_time_precise()}] Peer {self.my_id}: My block won consensus!")
                        asyncio.create_task(self.transaction_completed())
            except Exception as e:
                print(f"⛔ [ERROR {util.get_current_time_precise()}] Peer {self.my_id}: While adding block to chain: {e}")

            
            self.reset_block_consensus()
            self.chain.can_mine = True
            self.chain.is_mining = False
            self.chain.mined_block = None

    async def _handle_final_block_consensus(self, data):
        async with self.block_consensus_lock:
            if self.consensus_finalized:
                return

            winning_block = Block.from_dict(data.get("winning_block"))
            winning_sender = data.get("winning_sender")
            finalizer = data.get("finalizer")
            total_blocks = data.get("total_blocks")

            print(f"🏆 [RECV {util.get_current_time_precise()}] Peer {self.my_id}: Recived FINAL consensus from {finalizer}, total blocks in consensus {total_blocks}.")
            self.mined_block = winning_block
            self.consensus_finalized = True

            try:
                if self.chain.get_last_block().header.height != self.mined_block.header.height:
                    if Block.is_valid(self.mined_block, self.chain):
                        self.chain.add_to_block_to_chain(self.mined_block)
                        print(f"✅ [INFO {util.get_current_time_precise()}] Peer {self.my_id}: Final block added to chain:")
                        print(self.mined_block.header)
                        
                        
                        if self.current_transaction:
                            current_transaction_id = Transaction.from_dict(self.current_transaction.get("transaction")).id
                            asyncio.create_task(self.notify_client_transaction_result(
                                current_transaction_id,
                                True,
                                f"Transaction successfully added to blockchain in block {winning_block.header.height}"
                            ))
                        
                        asyncio.create_task(self.transaction_completed())
            except Exception as e:
                print(f"⛔ [ERROR {util.get_current_time_precise()}] Peer {self.my_id}: While addding winning block to local chain: {e}")
                
               
                if self.current_transaction:
                    current_transaction_id = Transaction.from_dict(self.current_transaction.get("transaction")).id
                    asyncio.create_task(self.notify_client_transaction_result(
                        current_transaction_id,
                        False,
                        f"Error adding transaction to blockchain: {str(e)}"
                    ))

            # reset state
            self.reset_block_consensus()
            self.chain.can_mine = True
            self.chain.is_mining = False
            self.chain.mined_block = None
            self.is_transaction_validation = False
            self.transaction_votes = []

    async def _handle_handshake(self, ws, data):
        
        peer_id = data.get("peer_id")
        peer_uri = data.get("uri")
        print(f"🤝 [RECV {util.get_current_time_precise()}] Peer {self.my_id}: HANDSHAKE from {peer_id} ({peer_uri})")

        
        self.incoming_peers[ws] = {"id": peer_id, "uri": peer_uri}
        self.known_peers[peer_id] = {"uri": peer_uri, "id": peer_id}

        
        await self.send_message(ws, "HANDSHAKE_ACK", {
            "peer_id": self.my_id,
            "uri": self.my_uri
        })

    async def _handle_client_get_chain(self, ws):

        response = {"chain": []}
        for block in self.chain.chain:
            response["chain"].append(block.to_dict())

        await ws.send(json.dumps(response, indent=4))

    async def _handle_handshake_ack(self, data):
        
        peer_id = data.get("peer_id")
        peer_uri = data.get("uri")
        print(f"🤝 [RECV {util.get_current_time_precise()}] Peer {self.my_id}: HANDSHAKE_ACK from {peer_id} ({peer_uri})")
        self.known_peers[peer_id] = {"uri": peer_uri, "id": peer_id}

    async def _handle_peers_list(self, sender_id, data):
        
        print(f"📋 [RECV {util.get_current_time_precise()}] Peer {self.my_id}: PEERS list from {sender_id}: {data}\n")
        for peer_info in data:
            peer_uri = peer_info.get("uri")
            peer_id = peer_info.get("id")
            if (peer_uri != self.my_uri and 
                peer_uri not in self.outgoing_peers and 
                peer_id != self.my_id):
                asyncio.create_task(self.connect_to_peer(peer_uri))

    def get_network_size(self):
        return len(self.known_peers) + 1  # +1 for self

    def calculate_required_votes(self):
        network_size = self.get_network_size()
        return int(network_size * self.consensus_threshold) + 1

    def _check_transaction_consensus(self):
        required_votes = self.calculate_required_votes()

        print(f"🗳️ [INFO {util.get_current_time_precise()}] Peer {self.my_id}: Required {str(required_votes)} voices.")

        def izdvoji_po_validnosti(lista):
            validne = [item for item in lista if item.get("vote") is True]
            nevalidne = [item for item in lista if item.get("vote") is False]
            return validne, nevalidne

        positive_votes, negative_votes = izdvoji_po_validnosti(self.transaction_votes)
        
        current_transaction_id = None
        if self.current_transaction:
            current_transaction_id = Transaction.from_dict(self.current_transaction.get("transaction")).id

        if len(positive_votes) >= required_votes:
            print(f"👥✅ [INFO {util.get_current_time_precise()}] Peer {self.my_id}: Transaction ACCEPTED by consensus")
            
            print(f"\n⛏️ [INFO {util.get_current_time_precise()}] Peer {self.my_id}: Mining started.")
            
            self.chain.can_mine = True
            self.chain.is_mining = True
            self.consensus_finalized = False
            
            mining_thread = threading.Thread(target=self.chain.create_new_block, daemon=True)
            mining_thread.start()

        else:
            print(f"👥❌ [INFO {util.get_current_time_precise()}] Peer {self.my_id}: Transaction REJECTED by consensus")
            
            if current_transaction_id:
                asyncio.create_task(self.notify_client_transaction_result(
                    current_transaction_id, 
                    False, 
                    f"Transaction rejected by network consensus. Positive votes: {len(positive_votes)}, Required: {required_votes}"
                ))
            
            asyncio.create_task(self.transaction_completed())

        self.is_transaction_validation = False
        self.transaction_votes = []

    def reset_block_consensus(self):
       
        self.received_blocks.clear()
        self.consensus_finalized = False
        #  mined_block saved until is finalized and added to block

    async def start_server(self):
        
        async def handler(ws):
            try:
                async for message in ws:
                    await self.handle_message(ws, message)
            finally:
                # Cleanup 
                if ws in self.incoming_peers:
                    peer_info = self.incoming_peers[ws]
                    print(f"  [INFO {util.get_current_time_precise()}] Peer {self.my_id}: Incoming peer {peer_info['id']} disconnected.")
                    del self.incoming_peers[ws]
                
                to_remove = []
                for transaction_id, client_ws in self.client_transactions.items():
                    if client_ws == ws:
                        to_remove.append(transaction_id)
                
                for transaction_id in to_remove:
                    print(f"🧹 [CLEANUP {util.get_current_time_precise()}] Peer {self.my_id}: Removing disconnected client transaction {transaction_id}")
                    del self.client_transactions[transaction_id]

        print(f"🚀 PEER {self.my_id} started on {self.my_uri} at {util.get_current_time_precise()}...\n")

        return await websockets.serve(handler, "localhost", self.port)

    async def connect_to_peer(self, uri):
        
        if uri == self.my_uri or uri in self.outgoing_peers:
            return

        retry_count = 0
        max_retries = 3

        while retry_count < max_retries:
            try:
                print(f"🔄 [INFO {util.get_current_time_precise()}] Peer {self.my_id}: Trying to connect to {uri} (attempt {retry_count + 1})")
                ws = await websockets.connect(uri)
                self.outgoing_peers[uri] = ws
                print(f"🔗 [INFO {util.get_current_time_precise()}] Peer {self.my_id}: Connected to {uri}")

                
                await self.send_message(ws, "HANDSHAKE", {
                    "peer_id": self.my_id,
                    "uri": self.my_uri
                })

               
                peer_list = [{"uri": info["uri"], "id": info["id"]} for info in self.known_peers.values()]
                peer_list.append({"uri": self.my_uri, "id": self.my_id})  # dodaj sebe
                await self.send_message(ws, "PEERS", peer_list)

                async for message in ws:
                    await self.handle_message(ws, message)

            except Exception as e:
                print(f"⚠️ [WARN {util.get_current_time_precise()}] Peer {self.my_id}: Cannot connect to {uri}: {e}")
                retry_count += 1
                if retry_count < max_retries:
                    await asyncio.sleep(2)
                else:
                    print(f"⛔ [ERROR {util.get_current_time_precise()}] Peer {self.my_id}: Falied to connect to {uri} after {max_retries} tries.")
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
        
        disconnected_peers = []

       
        for uri, ws in list(self.outgoing_peers.items()):
            try:
                await self.send_message(ws, msg_type, data)
                print(f"👥 [SENT {util.get_current_time_precise()}] Peer {self.my_id}: {msg_type} to {uri}")
            except Exception as e:
                print(f"⛔ [ERROR {util.get_current_time_precise()}] Peer {self.my_id}: Failed to send to {uri}: {e}")
                disconnected_peers.append(uri)

        for uri in disconnected_peers:
            if uri in self.outgoing_peers:
                del self.outgoing_peers[uri]
                
        print(f"🔍 [BROADCAST {util.get_current_time_precise()}] Peer {self.my_id}: Sent {msg_type} to {len(self.outgoing_peers)} outgoing peers \n")


    async def update_loop(self):
       
        while True:

           
            if self.is_transaction_validation and self.get_network_size() == len(self.transaction_votes):
                self._check_transaction_consensus()

          
            if self.chain.is_mining and not self.consensus_finalized:
                if self.chain.mined_block is not None:
                    block_to_send = self.chain.mined_block
                    # stop mining locally
                    self.chain.is_mining = False

                    print(f"\n📤 [INFO {util.get_current_time_precise()}] Peer {self.my_id}: Sending mined block to consensus.\n")
                    await self.broadcast("VERIFY_BLOCK", block_to_send.to_dict())

            await asyncio.sleep(0.1)  

    async def run(self, initial_peers=None):
       
        await self.start_server()

        print(f"📝 [INFO {util.get_current_time_precise()}] Peer {self.my_id}: Pending transactions queue initialized")

       
        if initial_peers:
            for peer_uri in initial_peers:
                if peer_uri != self.my_uri:
                    asyncio.create_task(self.connect_to_peer(peer_uri))

       
        asyncio.create_task(self.update_loop())

        while True:
            await asyncio.sleep(5)