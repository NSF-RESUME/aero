from datetime import datetime
from enum import IntEnum
from uuid import UUID
from uuid import uuid4
from typing import TYPE_CHECKING
from typing import Optional

from sqlmodel import Column
from sqlmodel import Field
from sqlmodel import JSON
from sqlmodel import Relationship
from sqlmodel import Session
from sqlmodel import SQLModel

from aero import GLOBUS_CLIENT
from aero.models.error import FLOW_TIMER_ERROR
from aero.models.error import ServiceError
from aero.globus.utils import FlowEnum
from aero.models.function import Function


if TYPE_CHECKING:  # pragma: nocover
    from aero.models.data import Data


class TriggerEnum(IntEnum):
    NONE = -1
    INGESTION = 0
    TIMER = 1
    ANY_INPUT = 2
    ALL_INPUT = 3


class FlowDerivation(SQLModel, table=True):
    __tablename__ = "flowderivation"
    flow_id: Optional[UUID] = Field(
        default=None, foreign_key="flow.id", primary_key=True
    )
    previous_data_id: Optional[UUID] = Field(
        default=None, foreign_key="data.id", primary_key=True
    )


class FlowContribution(SQLModel, table=True):
    __tablename__ = "flowcontribution"
    flow_id: Optional[UUID] = Field(
        default=None, foreign_key="flow.id", primary_key=True
    )
    produced_data_id: Optional[UUID] = Field(
        default=None, foreign_key="data.id", primary_key=True
    )


class Flow(SQLModel, table=True):
    __tablename__ = "flow"
    id: UUID = Field(
        default_factory=uuid4, index=True, primary_key=True
    )  # Column(Uuid, default=uuid4, index=True, primary_key=True)
    function_id: UUID | None = Field(
        foreign_key="function.id"
    )  # Column(Uuid, db.ForeignKey("function.id"))
    function_args: dict | list = Field(default_factory=dict, sa_column=Column(JSON))
    pull_function_id: UUID | None = Field(nullable=False)  # Column(Uuid)
    commit_function_id: UUID | None = Field(nullable=False)  # Column(Uuid)
    email: str | None = Field(default=None)  # Column(String)
    description: str | None = Field(default=None)  # Column(String)
    timer: int | None = Field(default=None)  # Column(Integer)
    timer_job_id: UUID | None = Field(default=None)  # Column(String)
    policy: int = Field(nullable=False)  # Column(Integer)
    last_executed: datetime | None = Field(default=None)  # Column(DateTime)
    user_endpoint: UUID | None = Field(default=None)  # Column(String)
    arg_hash: str | None = Field(default=None)  # Column(String)
    derived_from: list["Data"] = Relationship(link_model=FlowDerivation)
    contributed_to: list["Data"] = Relationship(link_model=FlowContribution)
    function: Optional["Function"] = Relationship()

    def _start_timer_flow(self, session: Session):
        self.timer_job_id = GLOBUS_CLIENT.set_timer(
            self.timer,
            self.id,
            self.email,
            FlowEnum.USER_FLOW,
            user_function=self.function_id,
            pull_function_uuid=self.pull_function_id,
            commit_function_uuid=self.commit_function_id,
            function_args=self.function_args,
            user_endpoint=self.user_endpoint,
        )

        return self.timer_job_id

    # TODO: remove all the execution-related parts from data and put in here
    def _start_ingestion_flow(self, session: Session, flush=False) -> UUID:
        if not flush and self.timer_job_id is not None:
            raise ServiceError(
                FLOW_TIMER_ERROR, "Flow already has a flow timer assigned"
            )

        self.timer_job_id = GLOBUS_CLIENT.set_timer(
            self.timer,
            self.id,
            self.email,
            FlowEnum.VERIFY_AND_MODIFY,
            user_function=self.function_id,
            pull_function_uuid=self.pull_function_id,
            commit_function_uuid=self.commit_function_id,
            function_args=self.function_args,
            user_endpoint=self.user_endpoint,
        )

        return self.timer_job_id

    def _run_flow(self, session: Session) -> int:
        # try:
        function_args = self.function_args
        # except json.JSONDecodeError as e:
        #     print(f"WARNING: Function args cannot be loaded: {e}")

        if self.policy == TriggerEnum.INGESTION:
            self._start_ingestion_flow(session=session)
        elif self.policy == TriggerEnum.TIMER:
            self._start_timer_flow(session=session)
            self.last_executed = datetime.now()
        elif self.policy == TriggerEnum.ANY_INPUT:  # ANY
            if self.last_executed is None or any(
                s.last_version().created_at > self.last_executed
                for s in self.derived_from
            ):
                GLOBUS_CLIENT.run_flow(
                    endpoint_uuid=self.user_endpoint,
                    function_uuid=self.function_id,
                    pull_function_uuid=self.pull_function_id,
                    commit_function_uuid=self.commit_function_id,
                    tasks=function_args,
                    email=self.email,
                )
                self.last_executed = datetime.now()

        elif self.policy == TriggerEnum.ALL_INPUT:  # ALL
            if self.last_executed is None or all(
                [
                    s.last_version().created_at > self.last_executed
                    for s in self.derived_from
                ]
            ):
                GLOBUS_CLIENT.run_flow(
                    endpoint_uuid=self.user_endpoint,
                    function_uuid=self.function_id,
                    pull_function_uuid=self.pull_function_id,
                    commit_function_uuid=self.commit_function_id,
                    tasks=function_args,
                    email=self.email,
                )
                self.last_executed = datetime.now()

        else:
            return self.policy

        session.add(self)
        session.commit()
        session.refresh(self)

        return self.policy


def create_flow(
    session: Session,
    derived_from: list["Data"],
    contributed_to: list["Data"],
    endpoint: UUID | None = None,
    arg_hash: str | None = None,
    function_id: UUID | None = None,
    pull_function_id: UUID | None = None,
    commit_function_id: UUID | None = None,
    description: str = "",
    function_args: dict | list = {"aero": {}},
    timer: int | None = None,
    policy: TriggerEnum = TriggerEnum.NONE,
    email: str | None = None,
):
    if policy == TriggerEnum.INGESTION and timer is None:
        timer = 86400

    last_executed = None
    id = uuid4()

    if isinstance(function_args, list):
        task_list = []
        task_invocation: dict = {}

        for fargs in function_args:
            fargs["aero"]["flow_id"] = str(id)

            task_invocation["kwargs"] = fargs
            task_invocation["function"] = str(function_id)
            task_invocation["endpoint"] = str(endpoint)

            task_list.append(task_invocation)

    else:
        task_list = {}
        function_args["aero"]["flow_id"] = str(id)
        task_list["kwargs"] = function_args
        task_list["function"] = str(function_id)
        task_list["endpoint"] = str(endpoint)

    function_args = task_list

    f = Flow(
        id=id,
        function_id=function_id,
        pull_function_id=pull_function_id,
        commit_function_id=commit_function_id,
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

    session.add(f)
    session.commit()

    f._run_flow(session=session)
    session.refresh(f)

    return f
