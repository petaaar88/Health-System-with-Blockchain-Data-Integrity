import os
from Crypto.PublicKey import RSA
from blockchain.backend.core.transaction import Transaction
from blockchain.backend.util import util

class Account:

    def __init__(self):
        _private_key = RSA.generate(2048)
        self.private_key = _private_key.export_key(format='DER').hex()
        self.public_key = _private_key.public_key().export_key(format='DER').hex()


    def get_raw_public_key(self):
        return RSA.import_key(bytes.fromhex(self.public_key))
    
    def get_raw_private_key(self):
        return RSA.import_key(bytes.fromhex(self.private_key))
    
    def sign(self,transaction: Transaction):
        signature = util.sign_data(util.object_to_canonical_bytes_json(transaction.body), self.get_raw_private_key())

        transaction.signature = signature
        
        return signature

    @staticmethod
    def _add_new_account_to_db(new_account,port):
        path = f"./blockchain/db/{port}_accounts.json"
        accounts = []
        if os.path.exists(path):
            accounts = util.read_from_json_file(path)
            if isinstance(accounts,list) is False:
                accounts = []
        
        accounts.append(new_account)
        util.write_to_json_file(path,accounts)


