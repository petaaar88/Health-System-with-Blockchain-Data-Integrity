from __future__ import annotations
import uuid
from blockchain.backend.core.transaction_body import TransactionBody
from blockchain.backend.util import util

class Transaction:
    def __init__(self, transaction_body:TransactionBody):
        self.signature:bytes = None
        self.body = transaction_body
        self.id = uuid.uuid4().hex

    @staticmethod
    def is_valid(transaction: Transaction, peer_id ,health_record):
        
        #Validacija transakcije
        #1. Provera da li postoje adrese u bazi
        #2. Proverava se da li je digitani potpis vaslidan
        #3. Proveraa se da li zdravstveni zapis sadrzi obavezna polja i da li transakcija sadrzi sva obavezna polja

        print(f"🔍 Transaction {transaction.id} Validation: ")
        accounts = util.read_from_json_file(f"./blockchain/db/{peer_id}_accounts.json")

        if isinstance(accounts,list) is False:
            print("❌ Addresses are invalid!")
            return False

        if not [a for a in accounts if a.get("public_key") == transaction.body.creator] or not [a for a in accounts if a.get("public_key") == transaction.body.patient]: 
            print("❌ Addresse is invalid!")
            return False

        print("✅ Addresses are valid.")

        bytes_object = util.object_to_canonical_bytes_json(transaction.body)

        if util.verify_signature(bytes_object, transaction.signature, util.get_raw_key(transaction.body.creator)) is False:
            return False

        required_keys = ["_id", "patient_id", "patient_first_name","patient_last_name","doctor_first_name","doctor_last_name","doctor_id","health_authority_name","health_authority_id"]

        if all(key in health_record for key in required_keys) is False or transaction.body.health_record_id == None or transaction.body.date is None:
            print(f"❌ Transaction {transaction.id} is invalid!") 
            return False

        if util.hash256(health_record) != transaction.body.health_record_hash:
            print(f"❌ Transaction {transaction.id} is invalid!") 
            return False

        print(f"✅ Transaction {transaction.id} is valid.")
    
    def __str__(self):
        return f"{self.body}"
    
    def to_dict(self):
        return {
            "id":self.id,
            "signature": self.signature.hex(),
            "body":self.body.to_dict() if hasattr(self.body, "to_dict") else None,
        }
    
    @staticmethod
    def from_dict(transaction_dict:dict):
        tx = Transaction(TransactionBody.from_dict(transaction_dict.get("body")))
        tx.signature = bytes.fromhex(transaction_dict.get("signature"))
        tx.id = transaction_dict.get("id")
        return tx





