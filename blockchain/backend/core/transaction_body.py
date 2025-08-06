class TransactionBody:
    def __init__(self, creator, patient, location,date,medical_record_hash:str = None):
        self.creator = creator
        self.patient = patient
        self.medical_record_hash = medical_record_hash
        self.date = date
        self.location = location

    def __str__(self):
        return f"{{\n     creator: {self.creator}, \n     patient: {self.patient}, \n     medical_record_hash: {self.medical_record_hash}, \n     location: {self.location}, \n     date: {self.date}\n   }}"