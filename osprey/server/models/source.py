from osprey.server.app import db
from osprey.server.lib.error import ServiceError, MODEL_INSUFFICIENT_ATTRS, FLOW_TIMER_ERROR
from sqlalchemy import Column, Integer, String, Date
from osprey.server.models.tag import SourceTagTable
from osprey.server.jobs.timer import set_timer

class Source(db.Model):
    id            = Column(Integer, primary_key=True)
    name          = Column(String)
    url           = Column(String)
    description   = Column(String)
    timer         = Column(Integer) # in seconds
    verifier      = Column(String)
    timer_job_id  = Column(String)
    last_refreshed= Column(Date)    # NOTE: Remove this, cause we can find it using timer_job_id
    versions      = db.relationship("SourceVersion", back_populates="source")
    tags          = db.relationship("Tag", secondary=SourceTagTable, back_populates="sources")

    # TODO: Validate duplicates and everything else
    def __init__(self, **kwargs):
        # validate
        kwargs = self._set_defaults(**kwargs)
        self._validate(**kwargs)

        # create
        super().__init__(**kwargs)
        db.session.add(self)
        db.session.commit()

        # after_create
        self._start_timer_flow()

    def __repr__(self):
        return "<Source(id={}, name='{}', url='{}', description={})>"\
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

    def _start_timer_flow(self, flush = False):
        if self.id is None:
            raise ServiceError(FLOW_TIMER_ERROR, "source needs to have an id")

        if not flush and self.timer_job_id is not None:
            raise ServiceError(FLOW_TIMER_ERROR, "source already has a flow timer")

        self.timer_job_id = set_timer(self.timer, self.name, self.id)
        db.session.add(self)
        db.session.commit()