import uuid
from blockchain.backend.core.account import Account

class Patient(Account):
    def __init__(self, first_name = None, last_name = None, personal_id = None, date_of_birth = None, gender = None, address = None, phone = None, citizenship = None, password = None):

        if(first_name == None and last_name == None):
            return
        
        super().__init__()
        
        self._id = uuid.uuid4().hex
        self.first_name = first_name
        self.last_name = last_name
        self.personal_id = personal_id
        self.date_of_birth = date_of_birth  # format: YYYY-MM-DD
        self.gender = gender
        self.address = address
        self.phone = phone
        self.citizenship = citizenship
        self.password = password

        self.health_records = []

    def to_dict(self):
        return {
            "_id": self._id,
            "password": self.password,
            "public_key": self.public_key,
            "private_key":self.private_key,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "personal_id": self.personal_id,
            "date_of_birth": self.date_of_birth,
            "gender": self.gender,
            "address": self.address,
            "phone": self.phone,
            "citizenship": self.citizenship,
            "health_records":self.health_records
        }
    
    @classmethod
    def from_dict(cls, data):
        
        patient = cls.__new__(cls)
        
        patient._id = data.get("_id")
        patient.public_key = data.get("public_key")
        patient.private_key = data.get("private_key")
        patient.password = data.get("password")
        patient.first_name = data.get("first_name")
        patient.last_name = data.get("last_name")
        patient.personal_id = data.get("personal_id")
        patient.date_of_birth = data.get("date_of_birth")
        patient.gender = data.get("gender")
        patient.address = data.get("address")
        patient.phone = data.get("phone")
        patient.citizenship = data.get("citizenship")
        patient.health_records = data.get("health_records", [])
        
        return patient
