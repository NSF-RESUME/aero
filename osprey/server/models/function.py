from app import db
from sqlalchemy import Column, Integer, String

class Function(db.Model):
    id          = Column(Integer, primary_key=True)
    uuid        = Column(String)
    provenances = db.relationship("Provenance", back_populates="function")

    def __repr__(self):
        return "<Function(id={}, source_version_id='{}')>".format(self.id, self.source_version.id)
