import logging

from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse
from uuid import UUID

import requests

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
from aero.models.data import create_data
from aero.models.data import Data
from aero.models.data_file import DataFile
from aero.models.data_version import DataVersion
from aero.models.flows import Flow
from aero.models.flows import TriggerEnum
from aero.models.source_type import SourceType
from aero.models.source_type import SourceUrl

from aero import GLOBUS_CLIENT

logger = logging.getLogger(__name__)

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
    # No-copy sources store no bytes, so the analysis pull needs the object's own
    # url. source_key identifies which registered url produced this version, and
    # trigger_url is that url resolved — so a run that wasn't triggered by this
    # source can still locate it.
    source_key: str | None = Field(default=None)
    no_copy: bool = Field(default=False)
    trigger_url: str | None = Field(default=None)


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


class SourceUrlOut(BaseModel):
    url: str = Field()
    object_key: str = Field()


class SourceTypeOut(BaseModel):
    name: str = Field()
    data_id: UUID = Field()
    no_copy: bool = Field(default=False)
    urls: list[SourceUrlOut] = Field(default_factory=list)


class SourceUrlIn(BaseModel):
    url: str = Field()


class SourceIn(BaseModel):
    """Create a source ``Data`` directly, with no flow attached."""

    name: str = Field()
    url: str = Field()
    type: str | None = Field(default=None)
    no_copy: bool = Field(default=False)
    collection_uuid: UUID | None = Field(default=None)
    collection_url: str | None = Field(default=None)
    description: str | None = Field(default=None)


def _type_out(st: SourceType) -> SourceTypeOut:
    return SourceTypeOut(
        name=st.name,
        data_id=st.data_id,
        no_copy=bool(st.data.no_copy) if st.data is not None else False,
        urls=[SourceUrlOut(url=u.url, object_key=u.object_key) for u in st.urls],
    )


def _register_source_url(session: Session, st: SourceType, url: str) -> SourceUrl:
    """Attach a URL to a type, rejecting a key already claimed elsewhere.

    The key is unique across all types: it is what a notify resolves on, so two
    types owning the same object would make resolution ambiguous by construction.
    """
    object_key = _normalize_object_key(url)
    clash = session.exec(
        select(SourceUrl).where(SourceUrl.object_key == object_key)
    ).first()
    if clash is not None:
        if clash.type_id == st.id:
            return clash
        raise HTTPException(
            status_code=409,
            detail=(
                f"Object key '{object_key}' is already registered to type "
                f"'{clash.type.name}'."
            ),
        )

    su = SourceUrl(type_id=st.id, url=url, object_key=object_key)
    session.add(su)
    session.commit()
    session.refresh(su)
    return su


def create_source_type(
    session: Session, name: str, data: Data, url: str | None = None
) -> SourceType:
    """Bind a new type to a Data, optionally registering its first URL."""
    existing = session.exec(select(SourceType).where(SourceType.name == name)).first()
    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Source type '{name}' already exists (data {existing.data_id}). "
                "Add a url to it instead of creating it again."
            ),
        )

    st = SourceType(name=name, data_id=data.id)
    session.add(st)
    session.commit()
    session.refresh(st)

    if url:
        _register_source_url(session, st, url)
        session.refresh(st)

    return st


@router.get("/types", response_model=list[SourceTypeOut])
def list_source_types(session: Session = Depends(get_session)):
    """Every notification type with its Data UUID and registered urls."""
    return [_type_out(st) for st in session.exec(select(SourceType)).all()]


@router.get("/types/{name}", response_model=SourceTypeOut)
def get_source_type(name: str, session: Session = Depends(get_session)):
    st = session.exec(select(SourceType).where(SourceType.name == name)).first()
    if st is None:
        raise HTTPException(status_code=404, detail=f"Source type '{name}' not found.")
    return _type_out(st)


@router.post("/types/{name}/urls", response_model=SourceTypeOut)
def add_source_type_url(
    name: str, payload: SourceUrlIn, session: Session = Depends(get_session)
):
    """Associate another URL with an existing type.

    The type's Data UUID is unchanged, so analysis flows already registered against
    it now also fire when this new URL changes.
    """
    st = session.exec(select(SourceType).where(SourceType.name == name)).first()
    if st is None:
        raise HTTPException(status_code=404, detail=f"Source type '{name}' not found.")

    _register_source_url(session, st, payload.url)
    session.refresh(st)
    return _type_out(st)


@router.post("/source", response_model=Data)
def create_source(payload: SourceIn, session: Session = Depends(get_session)):
    """Create a source ``Data`` with no flow attached.

    This is the no-copy create path: nothing is pulled, so there is no endpoint,
    no Globus function and no ingestion flow — the notify webhook records versions
    directly from the event metadata.
    """
    d = create_data(
        session=session,
        name=payload.name,
        url=payload.url,
        collection_uuid=payload.collection_uuid,
        collection_url=payload.collection_url,
        description=payload.description,
    )
    d.no_copy = payload.no_copy
    session.add(d)
    session.commit()
    session.refresh(d)

    if payload.type:
        create_source_type(session=session, name=payload.type, data=d, url=payload.url)
        session.refresh(d)

    return d


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

    return VersionOut(
        id=version.id,
        version=version.version,
        checksum=version.checksum,
        created_at=version.created_at,
        data_id=version.data_id,
        data=d,
        data_file=version.data_file,
        source_key=version.source_key,
        no_copy=bool(d.no_copy),
        trigger_url=_resolve_trigger_url(session, d, version.source_key),
    )


class NotifyIn(BaseModel):
    """Optional S3 event fields, accepted for traceability. Not required for the
    pull itself — the ingestion flow's download function re-fetches the source
    url, and the version metadata comes from the pulled file."""

    url: str | None = Field(default=None)  # per-run source url (e.g. MinIO presigned)
    key: str | None = Field(default=None)
    etag: str | None = Field(default=None)
    size: int | None = Field(default=None)
    # False treats this notify as a change even when the etag is unchanged.
    dedup: bool = Field(default=True)


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
    # False treats this notify as a change even when the etag is unchanged.
    dedup: bool = Field(default=True)


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


def _resolve_trigger_url(
    session: Session, data: Data, object_key: str | None
) -> str | None:
    """The stable registered url for an object key, falling back to ``Data.url``.

    Lets any run locate a no-copy source's bytes, not only the run its notify
    triggered — the signature is what can't be reconstructed, the url always can.
    """
    if object_key:
        su = session.exec(
            select(SourceUrl).where(SourceUrl.object_key == object_key)
        ).first()
        if su is not None:
            return su.url
    return data.url


def _resolve_notify_target(session: Session, file_id: str) -> tuple[Data, str, str]:
    """Resolve an object identity to ``(Data, object_key, trigger_url)``.

    Registered ``SourceUrl`` keys win and are an indexed exact lookup — the key is
    normalized once at registration rather than once per row per notify. Untyped
    sources fall back to the original ``Data.url`` scan, which skips typed Data so
    the two can't double-match.
    """
    target = _normalize_object_key(file_id)

    su = session.exec(
        select(SourceUrl).where(SourceUrl.object_key == target)
    ).first()
    if su is not None:
        return su.type.data, su.object_key, su.url

    candidates = session.exec(select(Data).where(Data.url != None)).all()
    matches = [
        d
        for d in candidates
        if d.source_type is None and _normalize_object_key(d.url) == target
    ]

    if not matches:
        raise HTTPException(
            status_code=404, detail=f"No source matches file_id '{file_id}'."
        )
    if len(matches) > 1:
        # Same bucket/key on multiple sources: break the tie on host+port+path.
        # If that doesn't resolve to exactly one (bare key, or unknown host), 409.
        full_target = _normalize_full_url(file_id)
        refined = [d for d in matches if _normalize_full_url(d.url) == full_target]
        if len(refined) != 1:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Ambiguous file_id '{file_id}': {len(matches)} sources "
                    "share this key and it could not be resolved by full URL."
                ),
            )
        matches = refined

    return matches[0], target, matches[0].url


def _change_metadata(
    etag: str | None, size: int | None, url: str | None
) -> tuple[str, int]:
    """Checksum + size for a no-copy version, HEADing the object if not supplied."""
    if etag is not None and size is not None:
        return etag.strip('"'), size

    if url:
        try:
            resp = requests.head(url, allow_redirects=True, timeout=30)
            if resp.status_code < 400:
                etag = etag or resp.headers.get("ETag")
                if size is None and resp.headers.get("Content-Length") is not None:
                    size = int(resp.headers["Content-Length"])
            else:
                logger.warning("HEAD %s returned %s", url, resp.status_code)
        except requests.RequestException as e:  # network/DNS/timeout
            logger.warning("HEAD %s failed: %s", url, e)

    if etag is None:
        raise HTTPException(
            status_code=400,
            detail=(
                "A no-copy notify needs an etag: send one in the payload, or make "
                "the object reachable by HEAD so it can be read from the response."
            ),
        )

    return etag.strip('"'), size if size is not None else 0


def _run_event_ingestion(
    session: Session,
    data: Data,
    trigger_url: str | None,
    signed_url: str | None,
    object_key: str,
    etag: str | None = None,
    size: int | None = None,
    dedup: bool = True,
) -> dict:
    """Record the change to ``data`` and trigger whatever it feeds.

    A no-copy source is handled inline: the version comes straight from the event
    metadata and no bytes move. Otherwise the ``INGESTION_EVENT`` flow contributing
    to this Data runs once (immediately, no timer) and pulls the object.

    ``signed_url`` is the transient per-run url (e.g. a MinIO presigned GET) and is
    never persisted; ``trigger_url`` is the stable registered url.
    """
    if data.no_copy:
        checksum, resolved_size = _change_metadata(
            etag, size, signed_url or trigger_url
        )
        suffix = Path(object_key).suffix.lstrip(".")

        result = data.add_new_version(
            session=session,
            new_file=object_key,
            format=suffix,
            checksum=checksum,
            size=resolved_size,
            created_at=datetime.now(),
            source_key=object_key,
            dedup=dedup,
        )

        if isinstance(result, dict):  # dedup hit: same object, same etag
            return {
                "status": "unchanged",
                "data_id": data.id,
                "source_key": object_key,
            }

        data.rerun_flow(
            session=session, trigger_url=trigger_url, signed_url=signed_url
        )
        version = data.last_version()
        return {
            "status": "version created",
            "data_id": data.id,
            "source_key": object_key,
            "version": version.version if version is not None else None,
        }

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

    flow._run_ingestion_flow(
        session=session,
        source_url=signed_url or trigger_url,
        source_key=object_key,
        dedup=dedup,
    )
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

    signed_url = payload.url if payload else None
    identity = (payload.key or payload.url) if payload else None

    if d.source_type is not None:
        # A typed source owns a known set of urls; work out which one fired so the
        # version records it and dedup is per-url. Unregistered urls are rejected.
        if identity is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Data {id} is type '{d.source_type.name}' with "
                    f"{len(d.source_type.urls)} registered urls — send 'key' or "
                    "'url' so the notify identifies which one changed."
                ),
            )
        target = _normalize_object_key(identity)
        match = next((u for u in d.source_type.urls if u.object_key == target), None)
        if match is None:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"'{identity}' is not a registered url of type "
                    f"'{d.source_type.name}'."
                ),
            )
        object_key, trigger_url = match.object_key, match.url
    else:
        object_key = _normalize_object_key(identity or d.url or str(id))
        trigger_url = d.url

    return _run_event_ingestion(
        session=session,
        data=d,
        trigger_url=trigger_url,
        signed_url=signed_url,
        object_key=object_key,
        etag=payload.etag if payload else None,
        size=payload.size if payload else None,
        dedup=payload.dedup if payload else True,
    )


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

    data, object_key, trigger_url = _resolve_notify_target(session, payload.file_id)

    return _run_event_ingestion(
        session=session,
        data=data,
        trigger_url=trigger_url,
        signed_url=payload.url,
        object_key=object_key,
        etag=payload.etag,
        size=payload.size,
        dedup=payload.dedup,
    )
