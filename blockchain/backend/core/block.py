from blockchain.backend.util import util
from blockchain.backend.core.transaction import Transaction
from blockchain.backend.core.block_header import BlockHeader

class Block:
    def __init__(self, block_header: BlockHeader, transaction: Transaction):
        self.header = block_header # meta podaci
        self.transaction = transaction
        self.header.merkle_root = util.hash256(transaction or "")

    def get_hash(self):
        return util.double_hash256(
            str(self.header.id) +
            (self.header.previous_block_hash or "") +
            (self.header.merkle_root or "") +
            str(self.header.timestamp) +
            str(self.header.height) +
            str(self.header.difficulty) +
            str(self.header.nonce) +
            str(self.header.miner) +
            str(self.transaction)
        )

    def mine(self):
        print("\n⛏️  Minning...")
        while not self.header.block_hash.startswith("0" * self.header.difficulty):
            self.header.nonce+=1
            self.header.block_hash = self.get_hash()

    def is_valid(self, medical_record:dict[str,any]):

        #Validacija bloka
        #1. Provera da li postoje adrese u bazi
        #2. Proverava se da li je digitani potpis vaslidan
        #3. Proveraa se da li zdravstveni zapis sadrzi obavezna polja i da li transakcija sadrzi sva obavezna polja

        print("🔍 Validation: ")
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
        
    def __str__(self):
        return f" {{\n{self.header} \n   Transaction: {self.transaction}\n }}"


        
