
from sqlalchemy import Column, Integer, String, Date
from app import db

class SourceVersion(db.Model):
    id            = Column(Integer, primary_key=True)
    version       = Column(Integer)
    checksum      = Column(String)
    created_at    = Column(Date)
    source_id     = Column(Integer, db.ForeignKey('source.id'))
    source        = db.relationship("Source", back_populates="versions")
    proxy         = db.relationship("Proxy", back_populates="source_version")

    # TODO: Make sure to have created_at as current time if it is not passed as an argument
    # NOTE: Also create a proxy automatically ig?

    # def __init__(self, *args, **kwargs):
    #     1. Set current_time if None
    #     2. super()

    def __repr__(self):
        return "<SourceVersion(id={}, version='{}', source_id='{}', proxy_id={})>"\
                .format(self.id, self.version, self.source_id, self.proxy_id)