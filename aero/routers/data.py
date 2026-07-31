from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Header
from fastapi import HTTPException
from fastapi import Query

from pydantic import BaseModel
from pydantic import Field

from sqlmodel import select
from sqlmodel import Session

from aero.auth import require_globus_auth
from aero.config import Config
from aero.database import get_session
from aero.models.data import Data
from aero.models.data_file import DataFile
from aero.models.data_version import DataVersion
from aero.models.flows import Flow
from aero.models.flows import TriggerEnum

from aero import GLOBUS_CLIENT

router = APIRouter(
    prefix="/data",
    tags=["data"],
    dependencies=[Depends(require_globus_auth)],
    responses={404: {"description": "Not found"}},
)

# Webhook routes use the shared-secret (X-Aero-Token) scheme instead of a Globus
# user token — the caller is an automated S3 event pipeline, not a Globus user —
# so they live on a separate router without the Globus auth dependency.
webhook_router = APIRouter(
    prefix="/data",
    tags=["webhook"],
    responses={404: {"description": "Not found"}},
)


class VersionOut(BaseModel):
    id: UUID = Field()
    version: int | None = Field(default=None)
    checksum: str | None = Field(default=None)
    created_at: datetime | None = Field(default=None)
    data_id: UUID | None = Field(default=None)
    data: Optional["Data"] = Field(default=None)
    data_file: Optional["DataFile"] = Field(default=None)


@router.get("/", response_model=list[Data])
# @authenticated
def all_data(
    offset: int = 0,
    limit: int = Query(default=15, le=15),
    session: Session = Depends(get_session),
):
    data = session.exec(
        select(Data).order_by(Data.id.desc()).offset(offset).limit(limit)
    ).all()
    return data


@router.get("/search")
# @authenticated
def search(query: str) -> dict:
    sc = GLOBUS_CLIENT.search_client

    try:
        result = sc.client.search(sc.index, query, advanced=True)
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))
    return result.data


@router.get("/{id}", response_model=Data)
# @authenticated
def get_data(id: UUID, session: Session = Depends(get_session)):
    d = session.exec(select(Data).where(Data.id == id)).first()
    if d is None:
        raise HTTPException(status_code=404, detail=f"Data with id {id} not found.")
    return d


@router.get("/{id}/versions", response_model=list[DataVersion])
# @authenticated
def list_versions(id: UUID, session: Session = Depends(get_session)):
    d = session.exec(select(Data).where(Data.id == id)).first()
    if d is None:
        raise HTTPException(status_code=404, detail=f"Data with id {id} not found.")

    return d.versions


@router.get("/{id}/latest", response_model=VersionOut)
# @authenticated
def get_latest(id: UUID, session: Session = Depends(get_session)):
    d = session.exec(select(Data).where(Data.id == id)).first()
    if d is None:
        raise HTTPException(status_code=404, detail=f"Data with id {id} not found.")

    version = d.last_version()

    if version is None:
        raise HTTPException(
            status_code=404, detail="No versions exist for this data ID."
        )
    return version


class NotifyIn(BaseModel):
    """Optional S3 event fields, accepted for traceability. Not required for the
    pull itself — the ingestion flow's download function re-fetches the source
    url, and the version metadata comes from the pulled file."""

    url: str | None = Field(default=None)  # per-run source url (e.g. MinIO presigned)
    key: str | None = Field(default=None)
    etag: str | None = Field(default=None)
    size: int | None = Field(default=None)


@webhook_router.post("/{id}/notify")
def notify_update(
    id: UUID,
    payload: NotifyIn | None = None,
    x_aero_token: str | None = Header(default=None),
    session: Session = Depends(get_session),
):
    """Webhook: an upstream source (e.g. an S3 object) changed.

    Runs the event-driven (INGESTION_EVENT) ingestion flow that produces this
    Data. The flow re-pulls the source and its commit function records a new
    version, which in turn triggers any dependent analysis flows.
    """
    if Config.WEBHOOK_SECRET is not None and x_aero_token != Config.WEBHOOK_SECRET:
        raise HTTPException(
            status_code=401, detail="Invalid or missing webhook token."
        )

    d = session.exec(select(Data).where(Data.id == id)).first()
    if d is None:
        raise HTTPException(status_code=404, detail=f"Data with id {id} not found.")

    flow = session.exec(
        select(Flow).where(
            Flow.contributed_to.any(id=id),
            Flow.policy == TriggerEnum.INGESTION_EVENT,
        )
    ).first()
    if flow is None:
        raise HTTPException(
            status_code=404,
            detail=f"No event-driven ingestion flow produces data {id}.",
        )

    source_url = payload.url if payload else None
    flow._run_ingestion_flow(session=session, source_url=source_url)
    return {"status": "ingestion triggered", "flow_id": flow.id, "data_id": id}
