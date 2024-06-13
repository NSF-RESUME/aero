from sqlalchemy import Column, Integer, String, ForeignKey

from osprey.worker.models.database import Base


class OutputVersion(Base):
    id = Column(Integer, primary_key=True)
    filename = Column(String)
    version = Column(Integer)
    checksum = Column(String)
    output_id = Column(Integer, ForeignKey("output.id"))
    provenance_id = Column(Integer, ForeignKey("provenance.id"))

    def __repr__(self):
        return f"<OutputVersion(id={self.id}, filename={self.filename}, version_id={self.version}, checksum={self.checksum})>"


"""

NOTE: This class is duplicated from the `class OutputVersion` from

    /osprey/server/models/output_version.py

But the usecase is, to separates the representation for different microservices

"""
