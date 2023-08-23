from osprey.server.app import db
from pathlib import Path
import json, csv, pickle
from osprey.server.lib.error import ServiceError, FILE_NOT_FOUND
from sqlalchemy import Column, Integer, LargeBinary, String

class SourceFile(db.Model):
    id                = Column(Integer, primary_key=True)
    file_name         = Column(String)
    file_type         = Column(String)
    source_version_id = Column(Integer, db.ForeignKey('source_version.id'))
    source_version    = db.relationship("SourceVersion", back_populates="source_file")
    encoding          = Column(String)

    def __init__(self, **kwargs):
        kwargs = self._set_defaults(**kwargs)
        super().__init__(**kwargs)
        self._write_file()

    def toJSON(self):
        with open(self._store_path(), 'r', newline='') as file:
            file_content = file.read()

        return {'file_name': self.file_name, 
                'file_type': self.file_type,
                'encoding': self.encoding,
                'file': file_content }

    def __repr__(self):
        return f"<SourceFile(id={self.id}, file_name={self.file_name})>"
    
    def _set_defaults(self, **kwargs):
        if 'encoding' not in kwargs:
            kwargs['encoding'] = 'utf-8'
        return kwargs

    def _decode_file(self, file):
        return file.decode(self.encoding)

    # NOTE: Change the path
    def _store_path(self):
        return f"/app/osprey/data/source/{self.source_version.source_id}/{self.source_version.version}/{self.file_name}"
    

    @property
    def file(self):
        file_path = self._store_path()
        if not Path(file_path).exists():
            raise ServiceError(FILE_NOT_FOUND, "Source file does not exist or was deleted")

        _file = open(file_path)
        if self.file_type == 'json':
            return json.loads(_file)

        return csv.reader(_file)
