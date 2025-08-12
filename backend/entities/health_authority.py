import uuid
from blockchain.backend.core.account import Account

class HealthAuthority(Account):
    def __init__(self, name, type, address, phone):
        super().__init__()
        
        self._id = uuid.uuid4().hex
        self.name = name
        self.type = type
        self.address = address
        self.phone = phone
        self.doctors = []
        self.patients = []

    def to_dict(self):
        return {
            "_id": self._id,
            "name": self.name,
            "type": self.type,
            "address": self.address,
            "phone": self.phone,
            "doctors": self.doctors,
            "patients": self.patients
        }
    
    
    @classmethod
    def from_dict(cls, data):
        """Kreira HealthAuthority objekat iz dict-a (iz MongoDB)"""
        authority = cls.__new__(cls)
        authority._id = data.get("id")
        authority.public_key = data.get("public_key")
        authority.private_key = data.get("private_key")
        authority.name = data.get("name")
        authority.type = data.get("type")
        authority.address = data.get("address")
        authority.phone = data.get("phone")
        authority.doctors = data.get("doctors")
        authority.patients = data.get("patients")
        
        return authority
