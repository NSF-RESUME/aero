from sqlalchemy import Column, Integer, String

from aero.app import db


class Function(db.Model):
    id = Column(Integer, primary_key=True)
    uuid = Column(String)
    provenances = db.relationship("Provenance", backref="function")

    def __init__(self, uuid: str):
        super().__init__(uuid=uuid)

        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return f"<Function(id={self.id}, uuid='{self.uuid}')>"

    def toJSON(self):
        return {
            "id": self.id,
            "uuid": self.uuid,
        }
