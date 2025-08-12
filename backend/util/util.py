import base64
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

