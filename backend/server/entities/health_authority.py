import uuid
from blockchain.backend.core.account import Account

class HealthAuthority(Account):
    def __init__(self, name = None, type = None, address = None, phone = None, password = None):

        if(name == None):
            return
        
        super().__init__()
        
        self._id = uuid.uuid4().hex
        self.name = name
        self.type = type
        self.address = address
        self.phone = phone
        self.password = password

        self.doctors = []
        self.patients = []

    def to_dict(self):
        return {
            "_id": self._id,
            "password": self.password,
            "public_key": self.public_key,
            "private_key":self.private_key,
            "name": self.name,
            "type": self.type,
            "address": self.address,
            "phone": self.phone,
            "doctors": self.doctors,
            "patients": self.patients
        }
    
    
    @classmethod
    def from_dict(cls, data):
       
        authority = cls.__new__(cls)
        authority._id = data.get("_id")
        authority.password = data.get("password"),
        authority.public_key = data.get("public_key")
        authority.private_key = data.get("private_key")
        authority.name = data.get("name")
        authority.type = data.get("type")
        authority.address = data.get("address")
        authority.phone = data.get("phone")
        authority.doctors = data.get("doctors")
        authority.patients = data.get("patients")
        
        return authority
