from sqlalchemy import Column
from sqlalchemy import Numeric
from sqlalchemy import String
from sqlalchemy import Uuid

from uuid import uuid4

from aero.app import db


class DataFile(db.Model):
    id = Column(Uuid, default=uuid4, index=True, primary_key=True)
    file_name = Column(String)
    file_type = Column(String)
    size = Column(Numeric)
    encoding = Column(String)
    version_id = Column(Uuid, db.ForeignKey("data_version.id"))
    version = db.relationship("DataVersion", back_populates="data_file", uselist=False)

    def __init__(self, **kwargs):
        kwargs = self._set_defaults(**kwargs)
        super().__init__(**kwargs)
        db.session.add(self)
        db.session.commit()

    def toJSON(self):
        return {
            "file_name": self.file_name,
            "collection_url": self.version.data.collection_url,
            "file_type": self.file_type,
            "file_size": self.size,
            "encoding": self.encoding,
        }

    def __repr__(self):
        return f"<DataFile(id={self.id}, file_name={self.file_name}, file_size={self.size}, encoding={self.encoding})>"

    def _set_defaults(self, **kwargs):
        if "encoding" not in kwargs:
            kwargs["encoding"] = "utf-8"
        return kwargs
