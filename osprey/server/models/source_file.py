from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import Numeric
from sqlalchemy import String

from osprey.server.app import db


class SourceFile(db.Model):
    id = Column(Integer, primary_key=True)
    file_name = Column(String)
    file_type = Column(String)
    size = Column(Numeric)
    encoding = Column(String)
    source_version_id = Column(Integer, db.ForeignKey("source_version.id"))
    source_version = db.relationship(
        "SourceVersion", back_populates="source_file", uselist=False
    )

    def __init__(self, **kwargs):
        kwargs = self._set_defaults(**kwargs)
        super().__init__(**kwargs)
        db.session.add(self)
        db.session.commit()

    def toJSON(self):
        return {
            "file_name": self.file_name,
            "collection_url": self.source_version.source.collection_url,
            "file_type": self.file_type,
            "file_size": self.size,
            "encoding": self.encoding,
        }

    def __repr__(self):
        return f"<SourceFile(id={self.id}, file_name={self.file_name}, file_size={self.size}, encoding={self.encoding})>"

    def _set_defaults(self, **kwargs):
        if "encoding" not in kwargs:
            kwargs["encoding"] = "utf-8"
        return kwargs
