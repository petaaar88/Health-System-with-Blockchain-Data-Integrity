import websocket
import threading
import time
import json

class BlockchainConnection:
    def __init__(self):
        self.ws = None
        self.connected = False
        self.response_received = False
        self.response_data = None
        
    def on_message(self, ws, message):
        print(f"Received from blockchain: {message}")
        self.response_data = message
        self.response_received = True
        
    def on_error(self, ws, error):
        print(f"WebSocket error: {error}")
        self.connected = False
        
    def on_close(self, ws, close_status_code, close_msg):
        print("WebSocket connection closed")
        self.connected = False
        
    def on_open(self, ws):
        print("Connected to blockchain WebSocket")
        self.connected = True
        
    def connect(self, timeout=5):
        """Kreira novu konekciju sa blockchain-om"""
        try:
            self.ws = websocket.WebSocketApp("ws://localhost:8765",
                                            on_open=self.on_open,
                                            on_message=self.on_message,
                                            on_error=self.on_error,
                                            on_close=self.on_close)
            
            # Pokretanje konekcije u background thread-u
            wst = threading.Thread(target=self.ws.run_forever)
            wst.daemon = True
            wst.start()
            
            # Čekanje da se uspostavi konekcija
            start_time = time.time()
            while not self.connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)
                
            return self.connected
        except Exception as e:
            print(f"Error connecting to blockchain: {e}")
            return False
            
    def send_message(self, message, timeout=10):
        """Šalje poruku na blockchain i čeka odgovor"""
        if not self.connected or not self.ws:
            return False, "Not connected to blockchain"
            
        try:
            self.response_received = False
            self.response_data = None
            
            self.ws.send(json.dumps(message))
            
            # Čekanje odgovora
            start_time = time.time()
            while not self.response_received and (time.time() - start_time) < timeout:
                time.sleep(0.1)
                
            if self.response_received:
                return True, self.response_data
            else:
                return False, "Timeout waiting for response"
                
        except Exception as e:
            print(f"Error sending to blockchain: {e}")
            return False, str(e)
            
    def disconnect(self):
        """Zatvara konekciju"""
        if self.ws:
            self.ws.close()
            self.connected = False


def send_to_blockchain_per_request(data, message):
    """Kreira novu konekciju za svaki request"""
    blockchain_conn = BlockchainConnection()
    
    # Uspostavi konekciju
    if not blockchain_conn.connect():
        return False, "Failed to connect to blockchain"
        
    try:
        # Pošalji poruku i čekaj odgovor
        success, response = blockchain_conn.send_message(message)
        return success, response
    finally:
        # Uvek zatvori konekciju nakon request-a
        blockchain_conn.disconnect()
