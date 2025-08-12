import uuid

class Doctor:

    def __init__(self, first_name, last_name, health_authority_id):
        self._id = uuid.uuid4().hex
        self.first_name = first_name
        self.last_name = last_name
        self.health_authority_id = health_authority_id

    def to_dict(self):
        return {
            "_id": self._id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "health_authority_id":self.health_authority_id
        }