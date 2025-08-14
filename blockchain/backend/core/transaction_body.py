class TransactionBody:
    def __init__(self, creator, patient, health_record_id,date,health_record_hash:str = None):
        self.creator = creator
        self.patient = patient
        self.health_record_hash = health_record_hash
        self.date = date
        self.health_record_id = health_record_id

    def __str__(self):
        return f"{{\n     creator: {self.creator}, \n     patient: {self.patient}, \n     health_record_hash: {self.health_record_hash}, \n     health_record_id: {self.health_record_id}, \n     date: {self.date}\n   }}"
    
    def to_dict(self):
        return {
            "creator": self.creator,
            "patient": self.patient,
            "health_record_hash": self.health_record_hash,
            "date": self.date ,
            "health_record_id": self.health_record_id
        }
    
    @staticmethod
    def from_dict(transaction_body_dict:str):
        return TransactionBody(transaction_body_dict.get("creator"),transaction_body_dict.get("patient"), transaction_body_dict.get("health_record_id"),transaction_body_dict.get("date"),transaction_body_dict.get("health_record_hash"))