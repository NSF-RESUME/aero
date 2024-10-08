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


flow_derivation = db.Table(
    "flow_derivation",
    Column("flow_id", Uuid, db.ForeignKey("flow.id")),
    Column("previous_data_id", Uuid, db.ForeignKey("data.id")),
)

flow_contribution = db.Table(
    "flow_contribution",
    Column("flow_id", Uuid, db.ForeignKey("flow.id")),
    Column("produced_data_id", Uuid, db.ForeignKey("data.id")),
)


class TriggerEnum(IntEnum):
    NONE = -1
    INGESTION = 0
    TIMER = 1
    ANY_INPUT = 2
    ALL_INPUT = 3


class Flow(db.Model):
    id = Column(Uuid, default=uuid4, index=True, primary_key=True)
    function_id = Column(Uuid, db.ForeignKey("function.id"))
    function_args = Column(String)
    email = Column(String)
    description = Column(String)
    timer = Column(Integer)
    timer_job_id = Column(String)
    policy = Column(Integer)
    last_executed = Column(DateTime)
    user_endpoint = Column(String)
    derived_from = db.relationship(
        "Data",
        secondary=flow_derivation,
        backref="input_data",
        uselist=True,
    )
    contributed_to = db.relationship(
        "Data", secondary=flow_contribution, backref="output_data", lazy=True
    )
    arg_hash = Column(String)

    def __init__(
        self,
        derived_from: list,
        contributed_to: list,
        endpoint: str,
        arg_hash: str,
        function_id: str | None = None,
        description: str = "",
        function_args: dict | list = {},
        timer: int | None = None,
        policy: TriggerEnum = TriggerEnum.NONE,
        email: str = "",
    ):
        if policy == TriggerEnum.INGESTION and timer is None:
            timer = 86400

        last_executed = None
        self.id = uuid4()

        super().__init__(
            id=self.id,
            function_id=function_id,
            derived_from=derived_from,
            contributed_to=contributed_to,
            description=description,
            function_args=function_args,
            timer=timer,
            policy=policy,
            last_executed=last_executed,
            user_endpoint=endpoint,
            arg_hash=arg_hash,
            email=email,
        )

        if isinstance(function_args, list):
            task_list = []
            task_invocation: dict = {}

            for fargs in self.function_args:
                fargs["aero"]["flow_id"] = str(self.id)

                task_invocation["kwargs"] = fargs
                task_invocation["function"] = str(self.function_id)
                task_invocation["endpoint"] = self.user_endpoint

                task_list.append(task_invocation)

        else:
            task_list = {}
            self.function_args["aero"]["flow_id"] = str(self.id)
            task_list["kwargs"] = self.function_args
            task_list["function"] = str(self.function_id)
            task_list["endpoint"] = self.user_endpoint

        self.function_args = json.dumps(task_list)

        db.session.add(self)
        db.session.commit()

        self._run_flow()

    def __repr__(self):
        return (
            f"<Flow(id={str(self.id)}, "
            f"derived_from={self.derived_from}, "
            f"contributed_to={self.contributed_to}, "
            f"function_id={str(self.function_id)}, "
            f"function_args='{self.function_args}', "
            f"timer={self.timer}, "
            f"timer_job_id='{self.timer_job_id}')>"
        )

    def toJSON(self):
        return {
            "id": str(self.id),
            "derived_from": [s.toJSON() for s in self.derived_from],
            "contributed_to": [o.toJSON() for o in self.contributed_to],
            "description": self.description,
            "endpoint": str(self.user_endpoint),
            "function_id": str(self.function_id),
            "function_args": self.function_args,
            "timer": self.timer,
            "policy": self.policy,
            "timer_job_id": self.timer_job_id,
            "last_executed": (
                self.last_executed.ctime()
                if self.last_executed is not None
                else self.last_executed
            ),
        }

    def _start_timer_flow(self):
        self.timer_job_id = set_timer(
            self.timer,
            self.id,
            "",
            FlowEnum.USER_FLOW,
            user_function=self.function_id,
            function_args=self.function_args,
            user_endpoint=self.user_endpoint,
        )
        db.session.add(self)
        db.session.commit()

        return self.timer_job_id

    # TODO: remove all the execution-related parts from data and put in here
    def _start_ingestion_flow(self, flush=False):
        if not flush and self.timer_job_id is not None:
            raise ServiceError(FLOW_TIMER_ERROR, "source already has a flow timer")

        self.timer_job_id = set_timer(
            self.timer,
            self.id,
            self.email,
            FlowEnum.VERIFY_AND_MODIFY,
            user_function=self.function_id,
            function_args=self.function_args,
            user_endpoint=self.user_endpoint,
        )
        db.session.add(self)
        db.session.commit()

    def _run_flow(self) -> int:
        try:
            function_args = json.loads(self.function_args)
        except json.JSONDecodeError as e:
            print(f"WARNING: Function args cannot be loaded: {e}")

        if self.policy == TriggerEnum.INGESTION:
            self._start_ingestion_flow()
        elif self.policy == TriggerEnum.TIMER:
            self._start_timer_flow()
            self.last_executed = datetime.now()
        elif self.policy == TriggerEnum.ANY_INPUT:  # ANY
            if self.last_executed is None or any(
                s.last_version().created_at > self.last_executed
                for s in self.derived_from
            ):
                run_flow(
                    endpoint_uuid=self.user_endpoint,
                    function_uuid=self.function_id,
                    tasks=function_args,
                )
                self.last_executed = datetime.now()
                db.session.add(self)
                db.session.commit()

        elif self.policy == TriggerEnum.ALL_INPUT:  # ALL
            if self.last_executed is None or all(
                s.last_version().created_at > self.last_executed
                for s in self.derived_from
            ):
                run_flow(
                    endpoint_uuid=self.user_endpoint,
                    function_uuid=self.function_id,
                    tasks=function_args,
                )
                self.last_executed = datetime.now()
                db.session.add(self)
                db.session.commit()

        return self.policy
