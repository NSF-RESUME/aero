from osprey.server.app import db
from osprey.server.lib.error import ServiceError, MODEL_INSUFFICIENT_ATTRS, FLOW_TIMER_ERROR
from sqlalchemy import Column, Integer, String, Date
from osprey.server.models.tag import SourceTagTable
from osprey.server.jobs.timer import set_timer
from osprey.server.lib.globus_flow import get_job, FlowEnum, FLOW_IDS
from osprey.server.config import Config

class Source(db.Model):
    id            = Column(Integer, primary_key=True)
    name          = Column(String)
    url           = Column(String)
    description   = Column(String)
    timer         = Column(Integer) # in seconds
    verifier      = Column(String)
    modifier      = Column(String)
    email         = Column(String)
    # Ensure to delete timer_job_id when either `verifier` or `modifier` is altered
    user_endpoint = Column(String)
    timer_job_id  = Column(String)
    flow_kind     = Column(Integer)
    versions      = db.relationship("SourceVersion", back_populates="source")
    tags          = db.relationship("Tag", secondary=SourceTagTable, back_populates="sources")

    # TODO: Validate duplicate source links and everything else
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
            'timer': self.timer,
            'verifier': self.verifier,
            'modifier': self.modifier,
            'email': self.email,
            'available_versions': len(self.versions)
        }

    def _validate(self, **kwargs):
        for attr in ['name', 'url', 'timer']:   # Required attributes
            if attr not in kwargs or not kwargs[attr]:
                raise ServiceError(code=MODEL_INSUFFICIENT_ATTRS, message="Name, url and timer values are required")

    def _set_defaults(self, **kwargs):
        if 'timer' not in kwargs:
            kwargs['timer'] = 86400 # 1 day
        if 'flow_kind' not in kwargs:
            if kwargs.get('verifier') is not None and kwargs.get('modifier') is not None:
                kwargs['flow_kind'] = FlowEnum.VERIFY_AND_MODIFY
            elif kwargs.get('verifier') is not None or kwargs.get('modifier') is not None:
                kwargs['flow_kind'] = FlowEnum.VERIFY_OR_MODIFY
            else:
                kwargs['flow_kind'] = FlowEnum.NONE
        
        if 'user_endpoint' not in kwargs:
            kwargs['user_endpoint'] = Config.GLOBUS_WORKER_UUID

        return kwargs

    def _start_timer_flow(self, flush = False):
        if self.id is None:
            raise ServiceError(FLOW_TIMER_ERROR, "source needs to have an id")

        if not flush and self.timer_job_id is not None:
            raise ServiceError(FLOW_TIMER_ERROR, "source already has a flow timer")

        self.timer_job_id = set_timer(self.timer, self.id, self.email, self.flow_kind)
        db.session.add(self)
        db.session.commit()
    
    # def _fake_flow(self):
    #     import osprey.worker.lib.globus_flow_helper as helper
    #     a, k = helper.download(source_id=self.id)
    #     helper.database_commit(*a, **k)
    
    def get_timer_job(self):
        return get_job(FLOW_IDS[self.flow_kind], self.timer_job_id)

    def last_refreshed_at(self):
        timer_job = self.get_timer_job()
        if timer_job is None:
            return
        return timer_job.get('last_ran_at')
    
    # TODO: Assuming the users are giving function UUID for now, and not getting us to register
    # NOTE: If they are registering their own functions, then they have to make sure to give our group access
    # Hence we need have a seperate routes for the to register functions or we enable `client.py` to hold the group_id, and hope the group_id doesnt change 