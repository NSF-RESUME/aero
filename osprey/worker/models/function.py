from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from osprey.worker.models.database import Base


class Function(Base):
    id = Column(Integer, primary_key=True)
    uuid = Column(String)
    provenances = relationship("Provenance", backref="function")

    def __repr__(self):
        return "<Function(id={}, uuid='{}')>".format(self.id, self.uuid)


"""

NOTE: This class is duplicated from the `class Function` from

    /osprey/server/models/function.py

But the usecase is, to separates the representation for different microservices

"""
