import uuid
from blockchain.backend.core.account import Account

class Patient(Account):
    def __init__(self, first_name, last_name):
        super().__init__()
        
        self.id = uuid.uuid4().hex
        self.first_name = first_name
        self.last_name = last_name
        
    

 