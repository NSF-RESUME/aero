import json

from datetime import datetime
from enum import IntEnum
from uuid import uuid4

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Uuid

from aero.app import db

from aero.automate.policy import run_flow
from aero.automate.timer import set_timer
from aero.globus.error import FLOW_TIMER_ERROR
from aero.globus.error import ServiceError
from aero.globus.utils import FlowEnum


provenance_derivation = db.Table(
    "provenance_derivation",
    Column("provenance_id", Uuid, db.ForeignKey("provenance.id")),
    Column("previous_data_id", Uuid, db.ForeignKey("data.id")),
)

provenance_contribution = db.Table(
    "provenance_contribution",
    Column("provenance_id", Uuid, db.ForeignKey("provenance.id")),
    Column("produced_data_id", Uuid, db.ForeignKey("data.id")),
)


class PolicyEnum(IntEnum):
    NONE = -1
    INGESTION = 0
    TIMER = 1
    ANY_INPUT = 2
    ALL_INPUT = 3


class Provenance(db.Model):
    id = Column(Uuid, default=uuid4, index=True, primary_key=True)
    function_id = Column(Uuid, db.ForeignKey("function.id"))
    function_args = Column(String)
    description = Column(String)
    timer = Column(Integer)
    timer_job_id = Column(String)
    policy = Column(Integer)
    last_executed = Column(DateTime)
    derived_from = db.relationship(
        "Data",
        secondary=provenance_derivation,
        backref="input_data",
        uselist=True,
    )
    contributed_to = db.relationship(
        "Data", secondary=provenance_contribution, backref="output_data", lazy=True
    )

    def __init__(
        self,
        function_id: str,
        derived_from: list,
        contributed_to: list,
        description: str = "",
        function_args: str = "",
        timer_job_id: str | None = None,
        timer: int | None = None,
        policy: PolicyEnum = PolicyEnum.NONE,
    ):
        if policy == 0 and timer is None:
            timer = 86400

        last_executed = None  # datetime.now()

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
        return f"<Provenance(id={self.id}, derived_from={self.derived_from}, contributed_to={self.contributed_to}, function_id={self.function_id}, function_args='{self.function_args}', timer={self.timer}, timer_job_id='{self.timer_job_id}')>"

    def toJSON(self):
        return {
            "id": self.id,
            "derived_from": [s.toJSON() for s in self.derived_from],
            "contributed_to": [o.toJSON() for o in self.contributed_to],
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

    def _start_ingestion_flow(self, flush=False):
        if not flush and self.timer_job_id is not None:
            raise ServiceError(FLOW_TIMER_ERROR, "source already has a flow timer")

        self.timer_job_id = set_timer(
            self.timer,
            self.id,
            self.email,
            FlowEnum.VERIFY_AND_MODIFY,
            user_endpoint=self.user_endpoint,
        )
        db.session.add(self)
        db.session.commit()

    def _run_flow(self) -> int:
        function_args = json.loads(self.function_args)

        if self.policy == PolicyEnum.INGESTION:
            self._start_ingestion_flow()
        elif self.policy == PolicyEnum.TIMER:
            self._start_timer_flow()
            self.last_executed = datetime.now()
        elif self.policy == PolicyEnum.ANY_INPUT:  # ANY
            if self.last_executed is None or any(
                s.last_version().created_at > self.last_executed
                for s in self.derived_from
            ):
                run_flow(
                    endpoint_uuid=function_args["endpoint"],
                    function_uuid=function_args["function"],
                    tasks=function_args["tasks"],
                )
                self.last_executed = datetime.now()
                db.session.add(self)
                db.session.commit()
        elif self.policy == PolicyEnum.ALL_INPUT:  # ALL
            if self.last_executed is None or all(
                s.last_version().created_at > self.last_executed
                for s in self.derived_from
            ):
                run_flow(
                    endpoint_uuid=function_args["endpoint"],
                    function_uuid=function_args["function"],
                    tasks=function_args["tasks"],
                )
                self.last_executed = datetime.now()
                db.session.add(self)
                db.session.commit()
        return self.policy
