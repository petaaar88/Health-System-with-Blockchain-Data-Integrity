from blockchain.backend.core.block import Block
from blockchain.backend.core.block_header import BlockHeader
from blockchain.backend.core.transaction import Transaction

class Chain:
    def __init__(self, miner, initial_time_to_mine = 30000, initial_difficulty = 5):
        self.difficulty = initial_difficulty
        self.time_to_mine = initial_time_to_mine
        self.miner = miner
        self.chain = [self.create_genesis_block()] 

    def create_genesis_block(self):
        genesis_block = Block(BlockHeader(0,self.difficulty,None,None),None)
        genesis_block.miner = None
        genesis_block.header.block_hash = genesis_block.get_hash()

        return genesis_block

    def get_last_block(self):
        return self.chain[-1]

    def add_block(self, transaction:Transaction, medical_record):

        last_block = self.get_last_block()
        new_block_height = last_block.header.height + 1

        block = Block(BlockHeader(new_block_height,self.difficulty,self.miner,last_block.header.block_hash),transaction)
        if Transaction.is_valid(transaction, medical_record) is False: #ovde treba van bloka da se proveri, ondnosno u transakciij i drugom metodi
            return None 
        
        block.mine()

        print("\n✔️  Blok uspešno iskopan")
        print(block)
        self.chain.append(block)
        
    def __str__(self):
        chain_to_string = "\nChain: \n[\n"
        for block in self.chain:
            chain_to_string +=str(block) + ",\n"

        return chain_to_string[:-2] + "\n]"