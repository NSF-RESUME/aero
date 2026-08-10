import hashlib
import uuid
import json

from copy import deepcopy
from datetime import datetime

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query

from pydantic import BaseModel
from pydantic import Field

from sqlmodel import select
from sqlmodel import Session

from typing import Optional

from aero.auth import require_globus_auth
from aero.database import get_session

from aero.models.flows import create_flow
from aero.models.flows import Flow
from aero.models.function import Function
from aero.models.data import Data
from aero.models.source_type import SourceType
from aero.routers.data import create_source_type

router = APIRouter(
    prefix="/flow",
    tags=["flow"],
    dependencies=[Depends(require_globus_auth)],
    responses={404: {"description": "Not found"}},
)


class FlowIn(BaseModel):
    gc_endpoint: uuid.UUID
    pull_function_uuid: Optional[uuid.UUID]
    commit_function_uuid: Optional[uuid.UUID]
    function_uuid: uuid.UUID = Field(default=uuid.UUID(int=0))
    input_data: dict = Field(default={})
    output_data: dict = Field(default={})
    description: str | None = Field(default=None)
    tags: list = Field(default=[])
    rule: int | None = Field(default=None)
    timer: int = Field(default=86400)
    email: str | None = Field(default=None)
    flow_kwargs: dict | list = Field(default={})


class FlowOut(BaseModel):
    id: uuid.UUID
    function_id: Optional[uuid.UUID]
    function_args: dict | list = Field(default_factory=dict)
    pull_function_id: uuid.UUID | None = Field(default=None)
    commit_function_id: uuid.UUID | None = Field(default=None)
    email: str | None = Field(default=None)
    description: str | None = Field(default=None)
    timer: int | None = Field(default=None)
    timer_job_id: uuid.UUID | None = Field(default=None)
    policy: int = Field(nullable=False)
    last_executed: datetime | None = Field(default=None)
    user_endpoint: uuid.UUID | None = Field(default=None)
    arg_hash: str | None = Field(default=None)
    derived_from: list["Data"] = Field(default_factory=list)
    contributed_to: list["Data"] = Field(default_factory=list)


def _flow_out(f: Flow) -> FlowOut:
    """Serialize a Flow with its two relationships.

    ``dict(f)`` yields the instance ``__dict__``, which includes any relationship
    SQLAlchemy has already loaded — so the two passed explicitly have to be
    dropped from it, or whether this raises "multiple values for keyword
    argument" depends on whether something upstream happened to touch them.
    """
    columns = {
        k: v for k, v in dict(f).items() if k not in ("derived_from", "contributed_to")
    }
    return FlowOut(
        **columns, contributed_to=f.contributed_to, derived_from=f.derived_from
    )


@router.get("/", response_model=list[FlowOut])
# @authenticated
def show_flows(
    offset: int = 0,
    limit: int = Query(default=15, le=15),
    session: Session = Depends(get_session),
):
    flows = session.exec(
        select(Flow).order_by(Flow.id.desc()).offset(offset).limit(limit)
    ).all()
    return [_flow_out(f) for f in flows]


@router.get("/{flow_id}", response_model=FlowOut)
# @authenticated
def get_flow(flow_id: uuid.UUID, session: Session = Depends(get_session)):
    f = session.exec(select(Flow).where(Flow.id == flow_id)).first()

    if f is None:
        raise HTTPException(
            status_code=404, detail=f"Flow with id {flow_id} was not found."
        )
    return _flow_out(f)


@router.post("/register", response_model=FlowOut)
# @authenticated
def register(fi: FlowIn, session: Session = Depends(get_session)):
    fl: Flow | None = None
    # check if function already exists

    f = session.exec(select(Function).where(Function.id == fi.function_uuid)).first()
    p_func = session.exec(
        select(Function).where(Function.id == fi.pull_function_uuid)
    ).first()
    c_func = session.exec(
        select(Function).where(Function.id == fi.commit_function_uuid)
    ).first()

    # The dedup hash must include output_data: two sources can share a function
    # and have identical (often empty) input_data/flow_kwargs yet be distinct
    # flows differing only by their output (e.g. INGESTION_EVENT sources with
    # different urls, all using the shared `stage` function). Hashing only
    # input_data/flow_kwargs would falsely collide them ("Flow already exists").
    all_args = deepcopy(fi.flow_kwargs)
    if isinstance(all_args, list):
        for aargs in all_args:
            aargs["input_data"] = fi.input_data
            aargs["output_data"] = fi.output_data
    else:
        all_args["input_data"] = fi.input_data
        all_args["output_data"] = fi.output_data

    arg_hash = hashlib.md5(
        json.dumps(all_args, sort_keys=True).encode("utf-8")
    ).hexdigest()

    # function does not already exist, so record it
    if f is None:
        f = Function(id=fi.function_uuid)
        session.add(f)
        session.commit()
        session.refresh(f)
    # TODO: Currently a bug here. Need to add a checksum for the flow
    else:  # function already exists, check if exact flow already exists
        fl = session.exec(
            select(Flow).where(Flow.function_id == f.id, Flow.arg_hash == arg_hash)
        ).first()

    if p_func is None:
        p_func = Function(id=fi.pull_function_uuid)
        session.add(p_func)
        session.commit()
        session.refresh(p_func)
    if c_func is None:
        c_func = Function(id=fi.commit_function_uuid)
        session.add(c_func)
        session.commit()
        session.refresh(c_func)

    if fl is None:  # flow does not already exist, so we can go ahead and register it
        contributed_to = []
        new_types = []

        for name, md in fi.output_data.items():
            if "url" in md:
                url = md["url"]
            else:
                url = None

            o = Data(
                name=name,
                url=url,
                collection_uuid=uuid.UUID(md["collection_uuid"]),
                collection_url=md["collection_url"],
                description=fi.description,
            )

            contributed_to.append(o)
            md["id"] = str(o.id)
            md["collection_url"] = o.collection_url
            md["collection_uuid"] = str(o.collection_uuid)

            # A copy-mode source can still be typed: the Data is born here, so bind
            # the type to it once the flow (and with it the Data) is committed. The
            # key is popped so it never reaches the worker kwargs.
            type_name = md.pop("type", None)
            if type_name:
                existing = session.exec(
                    select(SourceType).where(SourceType.name == type_name)
                ).first()
                if existing is not None:
                    raise HTTPException(
                        status_code=409,
                        detail=(
                            f"Source type '{type_name}' already exists (data "
                            f"{existing.data_id}). Add a url to it instead of "
                            "registering another flow."
                        ),
                    )
                new_types.append((type_name, o, url))

        derived_from = []

        for in_data in fi.input_data.values():
            d = session.exec(
                select(Data).where(Data.id == uuid.UUID(in_data["id"]))
            ).first()
            # add collection url to in_data
            in_data["collection_url"] = d.collection_url
            in_data["collection_uuid"] = str(d.collection_uuid)
            derived_from.append(d)

        flow_invocation = []
        if isinstance(fi.flow_kwargs, list):
            for fkw in fi.flow_kwargs:
                aero_data = {}
                aero_data["input_data"] = fi.input_data
                aero_data["output_data"] = fi.output_data
                aero_data["flow_id"] = None

                fkw["aero"] = aero_data

            flow_invocation.append(fkw)

        else:  # assume it's just a dict of kwargs
            aero_data = {}
            aero_data["input_data"] = fi.input_data
            aero_data["output_data"] = fi.output_data
            aero_data["flow_id"] = None

            fi.flow_kwargs["aero"] = aero_data

        fl = create_flow(
            session=session,
            function_id=f.id,
            pull_function_id=p_func.id,
            commit_function_id=c_func.id,
            derived_from=derived_from,
            description=fi.description,
            function_args=fi.flow_kwargs,
            policy=fi.rule,
            timer=fi.timer,
            contributed_to=contributed_to,
            endpoint=fi.gc_endpoint,
            email=fi.email,
            arg_hash=arg_hash,
        )

        # After create_flow, the output Data rows are persisted and can be bound to.
        for type_name, data_obj, url in new_types:
            create_source_type(
                session=session, name=type_name, data=data_obj, url=url
            )
    else:
        raise HTTPException(status_code=501, detail="Flow already exists")

    # dict(fl) yields the instance __dict__, which includes any relationship
    # SQLAlchemy has already loaded -- so drop the two passed explicitly rather
    # than depending on whether something upstream happened to touch them.
    columns = {
        k: v
        for k, v in dict(fl).items()
        if k not in ("derived_from", "contributed_to")
    }
    flow_o = FlowOut(
        **columns, derived_from=fl.derived_from, contributed_to=fl.contributed_to
    )

    return flow_o
