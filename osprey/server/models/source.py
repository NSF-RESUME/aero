from app import db
from sqlalchemy import Column, Integer, String
from models.tag import SourceTagTable

class Source(db.Model):
    id            = Column(Integer, primary_key=True)
    name          = Column(String)
    url           = Column(String)
    description   = Column(String)
    timer         = Column(Integer) # in seconds
    verifier      = Column(String)
    versions      = db.relationship("SourceVersion", back_populates="source")
    tags          = db.relationship("Tag", secondary=SourceTagTable, back_populates="sources")

    def __repr__(self):
        return "<Source(id={}, name='{}', url='{}', description={})>"\
                .format(self.id, self.name, self.url, self.description)