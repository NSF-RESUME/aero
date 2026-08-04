from datetime import datetime
from typing import Optional
from urllib.parse import urlparse
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


class NotifyByObjectIn(BaseModel):
    """Notify keyed by object identity instead of Data UUID.

    ``file_id`` is the object's *stable* identity — a full object URL or a bare
    ``bucket/key`` — used to resolve the Data record. ``url`` is the transient
    per-run source (e.g. a MinIO presigned GET) used only for this run's pull."""

    file_id: str = Field()  # object identity: full URL or bare "bucket/key"
    url: str | None = Field(default=None)  # per-run source url (e.g. presigned)
    key: str | None = Field(default=None)
    etag: str | None = Field(default=None)
    size: int | None = Field(default=None)


def _normalize_object_key(value: str) -> str:
    """Reduce an object URL (or bare ``bucket/key``) to a stable ``bucket/key``.

    Drops scheme, host, port, and query string so that a presigned URL, a plain
    object URL, and a bare ``bucket/key`` for the same object all compare equal:

        http://localhost:9000/traffic/report.xml.gz?X-Amz-Signature=... ->
        http://127.0.0.1:9000/traffic/report.xml.gz                     ->
        traffic/report.xml.gz                                           ->
            "traffic/report.xml.gz"
    """
    parsed = urlparse(value)
    # A scheme (http/https/s3/...) means host+path form; else treat as bucket/key.
    path = parsed.path if parsed.scheme else value
    return path.strip("/")


def _normalize_full_url(value: str) -> str:
    """Reduce a URL to ``host:port/path`` for disambiguating same-key sources.

    Keeps the netloc (host+port) that ``_normalize_object_key`` discards, so two
    sources sharing a ``bucket/key`` on different hosts can be told apart. Scheme
    and query are still dropped, so an ``http`` vs ``https`` or presigned-vs-plain
    URL for the same object still compares equal. A bare ``bucket/key`` (no host)
    normalizes to just the key, which won't match a host-qualified registered url.
    """
    parsed = urlparse(value)
    if parsed.scheme:
        return f"{parsed.netloc}{parsed.path}".strip("/")
    return value.strip("/")


def _require_webhook_token(x_aero_token: str | None) -> None:
    """Guard webhook routes with the shared secret when one is configured."""
    if Config.WEBHOOK_SECRET is not None and x_aero_token != Config.WEBHOOK_SECRET:
        raise HTTPException(
            status_code=401, detail="Invalid or missing webhook token."
        )


def _run_event_ingestion(session: Session, data: Data, source_url: str | None) -> dict:
    """Trigger the event-driven ingestion flow that produces ``data``.

    Looks up the ``INGESTION_EVENT`` flow contributing to this Data and runs it
    once (immediately, no timer). ``source_url`` overrides the registered source
    url for this run only (e.g. a MinIO presigned URL). Raises 404 if no such
    flow exists.
    """
    flow = session.exec(
        select(Flow).where(
            Flow.contributed_to.any(id=data.id),
            Flow.policy == TriggerEnum.INGESTION_EVENT,
        )
    ).first()
    if flow is None:
        raise HTTPException(
            status_code=404,
            detail=f"No event-driven ingestion flow produces data {data.id}.",
        )

    flow._run_ingestion_flow(session=session, source_url=source_url)
    return {"status": "ingestion triggered", "flow_id": flow.id, "data_id": data.id}


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
    _require_webhook_token(x_aero_token)

    d = session.exec(select(Data).where(Data.id == id)).first()
    if d is None:
        raise HTTPException(status_code=404, detail=f"Data with id {id} not found.")

    source_url = payload.url if payload else None
    return _run_event_ingestion(session=session, data=d, source_url=source_url)


@webhook_router.post("/notify")
def notify_by_object(
    payload: NotifyByObjectIn,
    x_aero_token: str | None = Header(default=None),
    session: Session = Depends(get_session),
):
    """Webhook: notify by object identity (``file_id``) instead of Data UUID.

    Resolves the Data record whose registered ``url`` normalizes to the same
    ``bucket/key`` as ``file_id``, then runs its event-driven ingestion flow.
    Lets an S3/MinIO event pipeline trigger ingestion knowing only the object
    it changed — not AERO's internal UUID.
    """
    _require_webhook_token(x_aero_token)

    target = _normalize_object_key(payload.file_id)
    candidates = session.exec(select(Data).where(Data.url != None)).all()
    matches = [d for d in candidates if _normalize_object_key(d.url) == target]

    if not matches:
        raise HTTPException(
            status_code=404, detail=f"No source matches file_id '{payload.file_id}'."
        )
    if len(matches) > 1:
        # Same bucket/key on multiple sources: break the tie on host+port+path.
        # If that doesn't resolve to exactly one (bare key, or unknown host), 409.
        full_target = _normalize_full_url(payload.file_id)
        refined = [d for d in matches if _normalize_full_url(d.url) == full_target]
        if len(refined) != 1:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Ambiguous file_id '{payload.file_id}': {len(matches)} sources "
                    "share this key and it could not be resolved by full URL."
                ),
            )
        matches = refined

    return _run_event_ingestion(
        session=session, data=matches[0], source_url=payload.url
    )
