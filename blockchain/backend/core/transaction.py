from __future__ import annotations
from blockchain.backend.core.transaction_body import TransactionBody
from blockchain.backend.util import util

class Transaction:
    def __init__(self, transaction_body:TransactionBody):
        self.signature = None
        self.body = transaction_body

    @staticmethod
    def is_valid(transaction: Transaction, medical_record):
        
        #Validacija transakcije
        #1. Provera da li postoje adrese u bazi
        #2. Proverava se da li je digitani potpis vaslidan
        #3. Proveraa se da li zdravstveni zapis sadrzi obavezna polja i da li transakcija sadrzi sva obavezna polja

        print("🔍 Transaction Validation: ")
        accounts = util.read_from_json_file("./blockchain/db/accounts.json")

        if isinstance(accounts,list) is False:
            print("❌ Addresses are invalid!")

        
        if [a for a in accounts if a.get("public_key") == transaction.body.creator] is False or [a for a in accounts if a.get("public_key") == transaction.body.patient] is False:
            print("❌ Addresse is invalid!")
            return False

        print("✅ Addresses are valid.")

        bytes_object = util.object_to_canonical_bytes_json(transaction.body)

        if util.verify_signature(bytes_object, transaction.signature, util.get_raw_key(transaction.body.creator)) is False:
            return False

        required_keys = ["id", "patient_id", "patient_name","doctor_name","doctor_id","hospital_name","hospital_id"]

        if all(key in medical_record for key in required_keys) is False or transaction.body.location == None or transaction.body.date is None:
            print("❌ Transaction is invalid!") 

        print("✅ Transaction is valid.")

        transaction.body.medical_record_hash = util.hash256(medical_record)
    
    def __str__(self):
        return f"{self.body}"



