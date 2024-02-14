from pathlib import Path

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from osprey.worker.models.database import Base


# TODO: Place in better location
GCS_OUTPUT_DIR = Path("/dsaas_storage/output")


class Output(Base):
    id = Column(Integer, primary_key=True)
    name = Column(String)
    provenance_id = Column(Integer, ForeignKey("provenance.id"))
    output_versions = relationship(
        "OutputVersion",
        backref="output_version",
        order_by="OutputVersion.version",
        lazy=True,
    )

    def __repr__(self):
        return f"<Output(id={self.id}, name={self.name}, provenance_id={self.provenance_id}, versions={self.output_versions})>"


"""

NOTE: This class is duplicated from the `class Output` from

    /osprey/server/models/output.py

But the usecase is, to separates the representation for different microservices

"""
