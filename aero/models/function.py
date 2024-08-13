from sqlalchemy import Column
from sqlalchemy import Uuid

from aero.app import db


class Function(db.Model):
    id = Column(Uuid, primary_key=True)
    provenances = db.relationship("Flow", backref="function")

    def __init__(self, uuid: str):
        super().__init__(id=uuid)

        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return f"<Function(id={self.id})>"

    def toJSON(self):
        return {
            "id": self.id,
        }
