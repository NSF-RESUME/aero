from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String

from osprey.server.app import db

from osprey.server.jobs.timer import set_timer
from osprey.server.lib.error import ServiceError
from osprey.server.lib.error import FLOW_TIMER_ERROR
from osprey.server.lib.globus_flow import FlowEnum

provenance_derivation = db.Table(
    "provenance_derivation",
    Column("provenance_id", Integer, db.ForeignKey("provenance.id")),
    Column("previous_source_version_id", Integer, db.ForeignKey("source_version.id")),
)


class Provenance(db.Model):
    id = Column(Integer, primary_key=True)
    function_id = Column(Integer, db.ForeignKey("function.id"))
    function_args = Column(String)
    description = Column(String)
    timer = Column(Integer)
    timer_job_id = Column(String)
    derived_from = db.relationship(
        "SourceVersion",
        secondary=provenance_derivation,
        backref="source_versions",
        uselist=True,
    )
    contributed_to = db.relationship("Output", backref="output", lazy=True)

    def __init__(
        self,
        function_id: str,
        derived_from: list,
        contributed_to: list,
        description: str = "",
        function_args: str = "",
        timer: int | None = None,
    ):
        db.session.add(self)
        db.session.commit()

        if timer is None:
            timer = 86400  # run daily

        super().__init__(
            function_id=function_id,
            derived_from=derived_from,
            contributed_to=contributed_to,
            description=description,
            function_args=function_args,
            timer=timer,
        )

    def __repr__(self):
        return "<Provenance(id={}, derived_from={}, contributed_to={}, function_id='{}', function_args='{}', timer='{}', 'timer_job_id='{}')>".format(
            self.id,
            self.derived_from,
            self.contributed_to,
            self.description,
            self.function_id,
            self.timer,
            self.timer_job_id,
        )

    def toJSON(self):
        return {
            "id": self.id,
            "derived_from": [v.toJSON() for v in self.derived_from],
            "contributed_to": self.contributed_to[0].toJSON()
            if len(self.contributed_to) > 0
            else None,
            "description": self.description,
            "function_id": self.function_id,
            "function_args": self.function_args,
            "timer": self.timer,
            "timer_job_id": self.timer_job_id,
        }

    def _start_timer_flow(self, flush=False):
        if self.id is None:
            raise ServiceError(FLOW_TIMER_ERROR, "source needs to have an id")

        if not flush and self.timer_job_id is not None:
            raise ServiceError(FLOW_TIMER_ERROR, "source already has a flow timer")

        # TODO: remove hard coding of email
        self.timer_job_id = set_timer(
            self.timer,
            self.id,
            "test@test.com",
            FlowEnum.USER_FLOW,
            **self.function_args,
        )
        db.session.add(self)
        db.session.commit()
