from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import Column, Integer, String, Date
from app import db
from models.proxy import Proxy

class SourceVersion(db.Model):
    id            = Column(Integer, primary_key=True)
    version       = Column(Integer)
    checksum      = Column(String)
    created_at    = Column(Date)
    source_id     = Column(Integer, db.ForeignKey('source.id'))
    source        = db.relationship("Source", back_populates="versions", uselist=False)
    proxy         = db.relationship("Proxy", back_populates="source_version", uselist=False)

    # TODO: Make sure to have created_at as current time if it is not passed as an argument
    # NOTE: Also create a proxy automatically ig?

    # def __init__(self, *args, **kwargs):
    #     1. Set current_time if None
    #     2. super()

    def __repr__(self):
        return "<SourceVersion(id={}, version='{}', source_id='{}')>"\
                .format(self.id, self.version, self.source_id)

    def toJSON(self):
        return {
            'id': self.id,
            'source': self.source.toJSON(),
            'version': self.version,
            'created_at': self.created_at
        }

    def create_proxy(self, replace=False):
        if self.proxy is not None and not replace:
            return self.proxy
        
        # TODO: Need to create representation
        proxy = Proxy(source_version=self)
        try:
            db.session.add(proxy)
            db.session.commit()
        except SQLAlchemyError as err:
            raise 
        return proxy