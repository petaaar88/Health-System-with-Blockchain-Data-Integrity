import base64
import websockets
import asyncio
import json
from bson import ObjectId, Binary
from dotenv import load_dotenv
import os

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad

def generate_secret_key_b64():
    key = get_random_bytes(16)
    return base64.b64encode(key).decode('utf-8')

def convert_secret_key_to_bytes(key):
    return base64.b64decode(key)

def encrypt(data, key):
    iv = get_random_bytes(16)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    ciphertext = cipher.encrypt(pad(data.encode(), AES.block_size))
    return iv + ciphertext

def decrypt(enc_data, key):
    iv = enc_data[:16]
    ciphertext = enc_data[16:]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    plaintext = unpad(cipher.decrypt(ciphertext), AES.block_size)
    return plaintext.decode("utf-8")

async def send_to_blockchain_and_wait_response(message, timeout=60):
   
    try:
        load_dotenv()
        uri = os.getenv("PEER_FOR_COMMUNICATION")
        
        async with websockets.connect(uri) as websocket:
            
            await websocket.send(json.dumps(message))
            print(f"📤 Sent to blockchain: {message['type']}")
            
           
            response = await asyncio.wait_for(websocket.recv(), timeout=timeout)
            response_data = json.loads(response)
            
            print(f"📥 Received from blockchain: {response_data}")
            return True, response_data
            
    except asyncio.TimeoutError:
        return False, {"error": "Blockchain response timeout"}
    except Exception as e:
        return False, {"error": f"Blockchain connection error: {str(e)}"}

def send_to_blockchain_per_request(message):
   
    try:
       
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            success, response = loop.run_until_complete(
                send_to_blockchain_and_wait_response(message)
            )
            return success, response
        finally:
            loop.close()
    except Exception as e:
        return False, {"error": f"Failed to communicate with blockchain: {str(e)}"}


def serialize_doc(doc):
    result = {}
    for key, value in doc.items():
        if isinstance(value, ObjectId):
            result[key] = str(value)
        elif isinstance(value, bytes):  # Ako je već Python bytes
            result[key] = value.decode("utf-8", errors="ignore")  # ili base64
        elif isinstance(value, Binary):  # Ako Mongo vrati Binary
            result[key] = value.decode("utf-8", errors="ignore")
        else:
            result[key] = value
    return result
