from aero.app import db
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Uuid

# NOTE: Does not auto-increment id, need to add migration
DataTagTable = db.Table(
    "data_tag",
    Column("id", Integer, primary_key=True),
    Column("data_id", Uuid, db.ForeignKey("data.id")),
    Column("tag_id", Integer, db.ForeignKey("tag.id")),
)


class Tag(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String)
    data = db.relationship(
        "Data", secondary=DataTagTable, back_populates="tags", uselist=True
    )

    def __init__(self, name, data=None):
        super().__init__(name=name, data=data)
        db.session.add(self)
        db.session.commit()

    def toJSON(self):
        return {"id": self.id, "name": self.name}

    def __repr__(self):
        return f"<Tag(id={self.id}, name='{self.name}')>"
