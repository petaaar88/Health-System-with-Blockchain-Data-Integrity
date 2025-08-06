from blockchain.backend.core.block import Block

class Chain:
    def __init__(self, initial_time_to_mine = 30000, initial_difficulty = 5):
        self.chain = [] 
        self.difficulty = initial_difficulty
        self.time_to_mine = initial_time_to_mine

    def get_last_block(self):
        return self.chain[-1]

    def add_block(self, block:Block):
        block.header.previous_block_hash = self.get_last_block().header.block_hash
        