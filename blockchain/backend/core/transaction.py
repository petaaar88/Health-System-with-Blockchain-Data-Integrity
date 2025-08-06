from blockchain.backend.core.transaction_body import TransactionBody

class Transaction:
    def __init__(self, transaction_body:TransactionBody):
        self.signature = None
        self.body = transaction_body



