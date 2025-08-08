class TransactionBody:
    def __init__(self, creator, patient, location,date,medical_record_hash:str = None):
        self.creator = creator
        self.patient = patient
        self.medical_record_hash = medical_record_hash
        self.date = date
        self.location = location

    def __str__(self):
        return f"{{\n     creator: {self.creator}, \n     patient: {self.patient}, \n     medical_record_hash: {self.medical_record_hash}, \n     location: {self.location}, \n     date: {self.date}\n   }}"
    
    def to_dict(self):
        return {
            "creator": self.creator,
            "patient": self.patient,
            "medical_record_hash": self.medical_record_hash,
            "date": self.date ,
            "location": self.location
        }
    
    @staticmethod
    def from_dict(transaction_body_dict:str):
        return TransactionBody(transaction_body_dict.get("creator"),transaction_body_dict.get("patient"), transaction_body_dict.get("location"),transaction_body_dict.get("date"),transaction_body_dict.get("medical_record_hash"))