import json

from datetime import datetime

from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import Integer
from sqlalchemy import String

from osprey.server.app import db

from osprey.server.jobs.user_flow import run_flow
from osprey.server.jobs.timer import set_timer
from osprey.server.lib.globus_flow import FlowEnum

provenance_derivation = db.Table(
    "provenance_derivation",
    Column("provenance_id", Integer, db.ForeignKey("provenance.id")),
    Column("previous_source_id", Integer, db.ForeignKey("source.id")),
)


class Provenance(db.Model):
    id = Column(Integer, primary_key=True)
    function_id = Column(Integer, db.ForeignKey("function.id"))
    function_args = Column(String)
    description = Column(String)
    timer = Column(Integer)
    timer_job_id = Column(String)
    policy = Column(Integer)
    last_executed = Column(Date)
    derived_from = db.relationship(
        "Source",
        secondary=provenance_derivation,
        backref="sources",
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
        timer_job_id: str | None = None,
        timer: int | None = None,
        policy: int | None = None,
    ):
        if policy is None:
            timer = -1  # run daily
            policy = 3
        elif policy == 0 and timer is None:
            timer = 86400

        last_executed = datetime.now()

        super().__init__(
            function_id=function_id,
            derived_from=derived_from,
            contributed_to=contributed_to,
            description=description,
            function_args=function_args,
            timer=timer,
            policy=policy,
            last_executed=last_executed,
        )

        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return "<Provenance(id={}, derived_from={}, contributed_to={}, function_id='{}', function_args='{}', timer='{}', 'timer_job_id='{}')>".format(
            self.id,
            self.derived_from,
            self.contributed_to,
            self.description,
            self.function_id,
            self.timer,
            self.policy,
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
            "policy": self.policy,
            "timer_job_id": self.timer_job_id,
            "last_executed": self.last_executed,
        }

    def _start_timer_flow(self):
        self.timer_job_id = set_timer(
            self.timer,
            self.id,
            "",
            FlowEnum.USER_FLOW,
            self.function_args,
        )
        db.session.add(self)
        db.session.commit()

    def _run_flow(self) -> int:
        function_args = json.loads(self.function_args)

        if self.policy == 0:
            self._start_timer_flow()
            return 0
        elif self.policy == 1:  # ANY
            if any(
                s.last_version().created_at < self.last_executed
                for s in self.derived_from
            ):
                run_flow(
                    endpoint_uuid=function_args["endpoint"],
                    function_uuid=function_args["function"],
                    tasks=function_args["tasks"],
                )
            return 1
        elif self.policy == 2:  # ALL
            if all(
                s.last_version().created_at < self.last_executed
                for s in self.derived_from
            ):
                run_flow(
                    endpoint_uuid=function_args["endpoint"],
                    function_uuid=function_args["function"],
                    tasks=function_args["tasks"],
                )
            return 2
        return 3
