class TransactionBody:
    def __init__(self, creator, patient, location,date,medical_record_hash:str = None):
        self.creator = creator
        self.patient = patient
        self.medical_record_hash = medical_record_hash
        self.date = date
        self.location = location
