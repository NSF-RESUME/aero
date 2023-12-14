from sqlalchemy import Column, Integer, String

from osprey.server.app import db


class OutputVersion(db.Model):
    id = Column(Integer, primary_key=True)
    filename = Column(String)
    version = Column(Integer)
    checksum = Column(String)
    source_id = db.Column(db.Integer, db.ForeignKey("output.id"))

    def __repr__(self):
        return f"<OutputVersion(id={self.id}, filename={self.filename}, version_id={self.version}, checksum={self.checksum})>"

    def toJSON(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "version": self.version,
            "checksum": self.checksum,
        }
