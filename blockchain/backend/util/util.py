import json
import datetime
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto.Signature import pss
from dataclasses import asdict


def double_hash256(s):
    # two rounds of sha265
    return  SHA256.new(SHA256.new(str(s).encode('utf-8')).digest()).hexdigest()

def hash256(s):
    return SHA256.new(str(s).encode('utf-8')).hexdigest()


def write_to_json_file(path:str, data:dict[str,any], mode = "w"):
    try:
        with open(path,mode,encoding='utf-8') as f:
            json.dump(data,f, indent=4, ensure_ascii=False)
    except Exception:
        print(f"Error while writing in {path} file!")
        return False

    return True

def read_from_json_file(path:str):
    data = None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"File {path} does not exist!") 
    except json.JSONDecodeError:
        print(f"Warning: {path} contains invalid JSON. Initializing with empty data.")
        return {}
    
    return data

def sign_data(data:bytes, key):

    data_hash = SHA256.new(data)

    signature = pss.new(key).sign(data_hash)

    return signature

def verify_signature(data:bytes, signature, key):

    data_hash = SHA256.new(data)

    try:
        pss.new(key).verify(data_hash, signature)
        print("✅ Signature is valid.")
    except (ValueError, TypeError):
        print("❌ Signature is invalid!")
        return False
    
    return True

def object_to_canonical_bytes_json(obj):
    
    if hasattr(obj, '__dict__'):
       
        data = obj.__dict__.copy()
    elif isinstance(obj, dict):
        data = obj
    elif hasattr(obj, '_asdict'):
        
        data = obj._asdict()
    else:
        
        try:
            data = asdict(obj)
        except:
            
            data = {"value": str(obj), "type": type(obj).__name__}
    
    json_str = json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    return json_str.encode('utf-8')


def get_raw_key(key:str):
    return RSA.import_key(bytes.fromhex(key))

def get_current_time_precise():
    trenutno_vreme = datetime.datetime.now()

    sati = trenutno_vreme.hour
    minuti = trenutno_vreme.minute
    sekunde = trenutno_vreme.second
   
    mikrosekunde = trenutno_vreme.microsecond

    return f"{sati:02d}:{minuti:02d}:{sekunde:02d}.{mikrosekunde:06d}"
