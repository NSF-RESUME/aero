from osprey.server.app import db
from sqlalchemy import Column, Integer, String

# NOTE: Does not auto-increment id, need to add migration
SourceTagTable = db.Table(
    "source_tag",
    Column("id", Integer, primary_key=True),
    Column("source_id", Integer, db.ForeignKey("source.id")),
    Column("tag_id", Integer, db.ForeignKey("tag.id")),
)


class Tag(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String)
    sources = db.relationship(
        "Source", secondary=SourceTagTable, back_populates="tags", uselist=True
    )

    def __init__(self, name, sources=None):
        super().__init__(name=name, sources=sources)
        db.session.add(self)
        db.session.commit()

    def toJSON(self):
        return {"id": self.id, "name": self.name}

    def __repr__(self):
        return f"<Tag(id={self.id}, name='{self.name}')>"
