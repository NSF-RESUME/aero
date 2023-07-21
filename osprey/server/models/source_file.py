from osprey.server.app import db
from sqlalchemy import Column, Integer, LargeBinary, String

class SourceFile(db.Model):
    id                = Column(Integer, primary_key=True)
    file_name         = Column(String)
    file              = Column(LargeBinary)
    source_version_id = Column(Integer, db.ForeignKey('source_version.id'))
    source_version    = db.relationship("SourceVersion", back_populates="source_file")
    encoding          = Column(String)

    def __init__(self, **kwargs):
        kwargs = self._set_defaults(**kwargs)
        super().__init__(**kwargs)

    def __repr__(self):
        return f"<SourceFile(id={self.id}, file_name={self.file_name})>"
    
    def _set_defaults(self, **kwargs):
        if 'encoding' not in kwargs:
            kwargs['encoding'] = 'utf-8'
        return kwargs

    def decode_file(self):
        return self.file.decode(self.encoding)
