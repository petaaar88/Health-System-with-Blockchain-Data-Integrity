
from datetime import datetime


class BlockHeader:
    def __init__(self, previous_block_hash, merkle_root, difficulty):
        self.previous_block_hash = previous_block_hash
        self.merkle_root = merkle_root # root merkle tree-a(hash tree), koje nastaje tako sto je svaki leaf transkacija iz bloka
        self.timestamp = datetime.now() #timestamp trenutnog bloka
        self.difficulty = difficulty #target difficulty
        self.nonce = 0
        self.block_hash = ''

  
    def mine(self, difficulty):
        self.difficulty = difficulty

        while not self.block_hash.startswith("0" * difficulty):
            self.nonce+=1
            self.block_hash = self.get_hash()


    def __str__(self):
        return f"Header {{ \n Previous block hash: {self.previous_block_hash},\n Timestamp: {self.timestamp},\n Nonce: {self.nonce},\n Difficulty: {self.difficulty}"

   