import uuid
from blockchain.backend.core.account import Account

class HealthAuthority(Account):
    def __init__(self, name):
        super().__init__()
        self.id = uuid.uuid4().hex
        self.name = name
