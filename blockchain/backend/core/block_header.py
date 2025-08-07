import uuid
from datetime import datetime


class BlockHeader:
    def __init__(self,height, difficulty, miner, previous_block_hash=None):
        self.height = height # redni broj bloka u blokchainu, krece od 0
        self.id = uuid.uuid4().hex
        self.previous_block_hash = previous_block_hash
        self.merkle_root = '' # root merkle tree-a(hash tree), koje nastaje tako sto je svaki leaf transkacija iz bloka
        self.timestamp = datetime.now() #timestamp trenutnog bloka
        self.difficulty = difficulty #target difficulty
        self.nonce = 0
        self.miner = miner
        self.block_hash = ''

    def __str__(self):
        return f"   Header: {{ \n     height: {self.height}, \n     id: {self.id}, \n     merkle root: {self.merkle_root}, \n     previous block hash: {self.previous_block_hash},\n     timestamp: {self.timestamp},\n     nonce: {self.nonce},\n     difficulty: {self.difficulty} \n     miner: {self.miner}, \n     block hash: {self.block_hash} \n   }},"

   