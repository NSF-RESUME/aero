from app import db
from app.error import ServiceError, MODEL_INSUFFICIENT_ATTRS
from sqlalchemy import Column, Integer, String
from models.tag import SourceTagTable

class Source(db.Model):
    id            = Column(Integer, primary_key=True)
    name          = Column(String)
    url           = Column(String)
    description   = Column(String)
    timer         = Column(Integer) # in seconds
    verifier      = Column(String)
    versions      = db.relationship("SourceVersion", back_populates="source")
    tags          = db.relationship("Tag", secondary=SourceTagTable, back_populates="sources")

    # TODO: Validate duplicates and everything else
    def __init__(self, **kwargs):
        kwargs = self._set_defaults(**kwargs)
        self._validate(**kwargs)
        super().__init__(**kwargs)

    def __repr__(self):
        return "<Source(id={}, name='{}', url='{}', descrip˝tion={})>"\
            .format(self.id, self.name, self.url, self.description)

    # TODO: Should send hash_id instead of id
    def toJSON(self):
        return { 
            'id': self.id, 
            'name': self.name, 
            'url': self.url, 
            'description': self.description,
            'timer': self.timer
        }

    def _validate(self, **kwargs):
        for attr in ['name', 'url', 'timer']:   # Required attributes
            if attr not in kwargs or not kwargs[attr]:
                raise ServiceError(code=MODEL_INSUFFICIENT_ATTRS, message="Name, url and timer values are required")

    def _set_defaults(self, **kwargs):
        if 'timer' not in kwargs:
            kwargs['timer'] = 86400 # 1 day
        return kwargs