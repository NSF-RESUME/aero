from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from osprey.worker.models.database import Base
import datetime

# Assume that this is sa read-only class
class SourceVersion(Base):
    __tablename__  = 'source_version'
    __table_args__ = {'extend_existing': True}
    id            = Column(Integer, primary_key=True)
    version       = Column(Integer)
    checksum      = Column(String)
    created_at    = Column(Date)
    source_id     = Column(Integer, ForeignKey('source.id'))
    source        = relationship("Source", back_populates="versions", uselist=False)
    source_file   = relationship("SourceFile", back_populates="source_version", uselist=False, lazy=False)

    def __init__(self, **kwargs):
        kwargs = self._set_defaults(**kwargs)
        super().__init__(**kwargs)

    def __repr__(self):
        return f"SourceVersion(id={self.id}, version={self.version}, source_id={self.source_id}, file_id={None if self.source_file is None else self.source_file.id})"

    def _set_defaults(self, **kwargs):
        if 'created_at' not in kwargs:
            kwargs['created_at'] = datetime.datetime.now()
        return kwargs

"""

NOTE: This class is duplicated from the `class SourceVersion` from

    /osprey/server/models/source_version.py

But the usecase is, to seperates the representation for different microservices

"""