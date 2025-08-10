from __future__ import annotations
from blockchain.backend.core.block import Block
from blockchain.backend.core.block_header import BlockHeader
from blockchain.backend.core.transaction import Transaction

class Chain:
    def __init__(self, miner, initial_time_to_mine = 30000, initial_difficulty = 5):
        self.difficulty = initial_difficulty
        self.time_to_mine = initial_time_to_mine #TODO ako stignem da namestim da se automatski podesava vreme kopanja
        self.miner = miner
        self.chain = [self.create_genesis_block()] 
        self.tx = None
        self.medical_record = None
        self.mined_block = None
        self.is_mining = False
        self.can_mine = True
        

    def create_genesis_block(self):
        genesis_block = Block(BlockHeader(0,self.difficulty,None,"0"*64),None)
        genesis_block.miner = None
        genesis_block.header.id = "1"
        genesis_block.header.timestamp = ""
        genesis_block.header.block_hash = genesis_block.get_hash()

        return genesis_block

    def get_last_block(self):
        return self.chain[-1]

    def create_new_block(self):
        
        self.is_mining = True

        last_block = self.get_last_block()
        new_block_height = last_block.header.height + 1

        block = Block(BlockHeader(new_block_height,self.difficulty,self.miner,last_block.header.block_hash),self.tx)
        
        block.mine(self)

        self.mined_block = block

        return block
    
    def add_to_block_to_chain(self, block: Block):
        
        self.chain.append(block)

        self.tx = None
        self.medical_record = None
        
    def add_transaction(self, transaction:Transaction, medical_record):
        if Transaction.is_valid(transaction, medical_record) is False:
            return False 
         
        self.tx = transaction
        self.medical_record = medical_record

        return True
         
    @staticmethod
    def is_valid(chain: Chain):
        for i in range(1, len(chain.chain)):
            current_block:Block = chain.chain[i]
            prev_block:Block = chain.chain[i - 1]

            if current_block.header.previous_block_hash == "0"*64 and current_block.header.miner == None  and current_block.header.height == 0:
                continue
            else:
                if (
                    current_block.header.block_hash != current_block.get_hash()
                    or prev_block.header.block_hash != current_block.header.previous_block_hash
                ):
                    print(f"❌ {chain.miner} Node chain is invalid!")
                    return False
            
        print(f"\n✅ {chain.miner} Node chain is valid.")
        return True


    def __str__(self):
        chain_to_string = "\nChain: \n[\n"
        for block in self.chain:
            chain_to_string +=str(block) + ",\n"

        return chain_to_string[:-2] + "\n]"