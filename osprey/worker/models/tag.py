from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship
from osprey.worker.models.database import Base

SourceTagTable = Table(
    "source_tag",
    Base.metadata,
    Column("id", Integer, primary_key=True),
    Column("source_id", Integer, ForeignKey("source.id")),
    Column("tag_id", Integer, ForeignKey("tag.id")),
)


# Assume that this is sa read-only class
class Tag(Base):
    __tablename__ = "tag"
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True)
    name = Column(String)
    sources = relationship("Source", secondary=SourceTagTable, back_populates="tags")

    def __repr__(self):
        return "<Tag(id={}, name='{}')>".format(self.id, self.name)


"""

NOTE: This class is duplicated from the `class Tag` from

    /osprey/server/models/tag.py

But the usecase is, to separates the representation for different microservices

"""
