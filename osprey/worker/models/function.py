from osprey.server.app import db
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

class Function(db.Model):
    id          = Column(Integer, primary_key=True)
    uuid        = Column(String)
    provenances = relationship("Provenance", backref="function")

    def __init__(self, uuid:str):
        super().__init__(uuid=uuid)
        

    def __repr__(self):
        return "<Function(id={}, uuid='{}')>".format(self.id, self.uuid)
    
    def toJSON(self):
        return {
            'id': self.id,
            'uuid': self.uuid
        }
        

    
