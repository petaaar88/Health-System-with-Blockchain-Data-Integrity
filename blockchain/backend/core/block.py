from blockchain.backend.util import util
from blockchain.backend.core.transaction import Transaction
from blockchain.backend.core.block_header import BlockHeader

class Block:
    def __init__(self,height, block_header: BlockHeader, transaction: Transaction):
        self.height = height # redni broj bloka u blokchainu, krece od 0
        self.header = block_header # meta podaci
        self.transaction = transaction

    def get_hash(self):
        return util.double_hash256(self.block_header.previous_block_hash + self.block_header.merkle_root + str(self.block_header.timestamp) + str(self.block_header.difficulty) + str(self.block_header.nonce))

    def is_valid(self, medical_record:dict[str,any]):

        #Validacija bloka
        #1. Provera da li postoje adrese u bazi
        #2. Proverava se da li je digitani potpis vaslidan
        #3. Proveraa se da li zdravstveni zapis sadrzi obavezna polja i da li transakcija sadrzi sva obavezna polja

        accounts = util.read_from_json_file("./blockchain/db/accounts.json")

        if isinstance(accounts,list) is False:
            print("❌ Adrese su nevalidne.")

        
        if [a for a in accounts if a.get("public_key") == self.transaction.body.creator] is False or [a for a in accounts if a.get("public_key") == self.transaction.body.patient] is False:
            print("❌ Adresa nije nevalidna.")
            return False

        print("✅ Adrese su validne.")

        bytes_object = util.object_to_canonical_bytes_json(self.transaction.body)

        if util.verify_signature(bytes_object, self.transaction.signature, util.get_raw_key(self.transaction.body.creator)) is False:
            return False

        required_keys = ["id", "patient_id", "patient_name","doctor_name","doctor_id","hospital_name","hospital_id"]

        if all(key in medical_record for key in required_keys) is False or self.transaction.body.location == None or self.transaction.body.date is None:
            print("❌ Transakcija je nevalidna.") 

        print("✅ Transakcija je validna.")

        self.transaction.body.medical_record_hash = util.hash256(medical_record)

        return True
        


        
