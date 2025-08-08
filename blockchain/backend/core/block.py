from __future__ import annotations
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
        print(f"\n⛏️  #{self.header.height} Block Minning...")
        while not self.header.block_hash.startswith("0" * self.header.difficulty):
            self.header.nonce+=1
            self.header.block_hash = self.get_hash()

        print(f"\n✔️  #{self.header.height} Blok successfully mined by {self.header.miner}.\n") #TODO ovde ide majner iz bloka koji je izmajnovao
        print(self)

    @staticmethod
    def is_valid(block:Block, chain):

        #Validacija bloka
        #1. Provera da li blok povezan sa chain-om
        #2. Proverava se da li ima validnu transakciju
        #3. Proveraa se da li ima dobar merkle root
        #4. Proverava se hash, odnosno resenje proof of work-a

        print(f"🔍 #{block.header.height} Block Validation: \n")

        if block.header.previous_block_hash != chain.get_last_block().header.block_hash:
            print("❌ Invalid block - Invalid previous block hash!")
            return False
        
        if Transaction.is_valid(block.transaction,chain.medical_record) is False:
            print("❌ Invalid block - invalid transaction!")
            return False
        
        if block.header.merkle_root != util.hash256(block.transaction or ""):
            print("❌ Invalid block - Invalid merkle root!")
            return False

        if block.header.block_hash != block.get_hash():
            print("❌ Invalid block - Invalid block hash!")
            return False
        
        print(f"\n✅ #{block.header.height} Block is valid.")

        return True
        
    def __str__(self):
        return f" {{\n{self.header} \n   Transaction: {self.transaction}\n }}"

    def to_dict(self):
        return {
            "header": self.header.to_dict() if hasattr(self.header, "to_dict") else None,
            "transaction": self.transaction.to_dict()  if hasattr(self.transaction, "to_dict") else None
        }

        
