from sqlalchemy import Column, Integer, String

from aero.app import db


class OutputVersion(db.Model):
    id = Column(Integer, primary_key=True)
    filename = Column(String)
    version = Column(Integer)
    checksum = Column(String)
    output_id = db.Column(db.Integer, db.ForeignKey("output.id"))
    output = db.relationship(
        "Output",
        back_populates="output_versions",
        lazy=True,
    )
    # provenance_id = Column(Integer, ForeignKey("provenance.id"))

    def __init__(self, filename: str, version: int, checksum: str, output_id: int):
        super().__init__(
            filename=filename, version=version, checksum=checksum, output_id=output_id
        )
        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return f"<OutputVersion(id={self.id}, filename='{self.filename}', version_id={self.version}, checksum='{self.checksum}')>"

    def toJSON(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "version": self.version,
            "checksum": self.checksum,
            "output": self.output.toJSON(),
        }
