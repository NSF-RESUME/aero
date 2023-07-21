from sqlalchemy import Column, Integer, String, LargeBinary, ForeignKey
from sqlalchemy.orm import relationship
from osprey.worker.models.database import Base

from osprey.worker.lib.serializer import decode

# Assume that this is sa read-only class
class SourceFile(Base):
    __tablename__ = 'source_file'
    id                = Column(Integer, primary_key=True)
    file_name         = Column(String)
    file              = Column(LargeBinary)
    source_version_id = Column(Integer, ForeignKey('source_version.id'))
    encoding          = Column(String)
    source_version    = relationship("SourceVersion", back_populates="source_file", uselist=False)

    def __repr__(self):
        return f"SourceFile(id={self.id}, file_name={self.file_name}, encoding={self.encoding}, source_version_id={self.source_version_id})"

    def get_file(self):
        return decode(self.file, self.encoding)
"""

NOTE: This class is duplicated from the `class SourceFile` from

    /osprey/server/models/source_file.py

But the usecase is, to seperates the representation for different microservices

"""