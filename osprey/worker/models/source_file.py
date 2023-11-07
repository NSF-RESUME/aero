from sqlalchemy import Column, Integer, String, LargeBinary, ForeignKey
from sqlalchemy.orm import relationship
from osprey.worker.models.database import Base
from pathlib import Path
from osprey.worker.lib.serializer import decode
from osprey.worker.models.utils import DOWNLOAD_DIR

# Assume that this is sa read-only class
class SourceFile(Base):
    __tablename__ = 'source_file'
    __table_args__ = {'extend_existing': True}
    id                = Column(Integer, primary_key=True)
    file_name         = Column(String)
    file_type         = Column(String)
    source_version_id = Column(Integer, ForeignKey('source_version.id'))
    encoding          = Column(String)
    source_version    = relationship("SourceVersion", back_populates="source_file", uselist=False)

    def __init__(self, **kwargs):
        kwargs = self._write_file(**kwargs)
        super().__init__(**kwargs)

    def _write_file(self, **kwargs):
        args = kwargs['args']
        file_name = kwargs['file_name']
        basename = Path(file_name).name
        ext = kwargs['file_type']

        file_path = Path(DOWNLOAD_DIR, f"source/{args['source_id']}/{args['version']}")
        file_path.mkdir(parents=True, exist_ok=True)
        fn = (file_path / basename).with_suffix(ext)
        Path(file_name).rename(fn)

        kwargs['file_name'] = fn
        kwargs.pop('args')
        return kwargs

    def __repr__(self):
        return f"SourceFile(id={self.id}, file_name={self.file_name}, encoding={self.encoding}, source_version_id={self.source_version_id})"

    @property
    def file(self):
        pass
"""

NOTE: This class is duplicated from the `class SourceFile` from

    /osprey/server/models/source_file.py

But the usecase is, to seperates the representation for different microservices

"""