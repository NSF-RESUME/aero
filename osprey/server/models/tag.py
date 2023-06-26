from app import db
from sqlalchemy import Column, Integer, String

# NOTE: Does not auto-increment id, need to add migration
SourceTagTable = db.Table("source_tag",
                    Column('id', Integer, primary_key=True),
                    Column('source_id', Integer, db.ForeignKey('source.id')),
                    Column('tag_id', Integer, db.ForeignKey('tag.id')))

class Tag(db.Model):
    id        = Column(Integer, primary_key=True)
    name      = Column(String)
    sources   = db.relationship("Source", secondary=SourceTagTable, back_populates="tags")

    def __repr__(self):
        return "<Tag(id={}, name='{}')>".format(self.id, self.name)