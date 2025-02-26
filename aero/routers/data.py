from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query

from sqlmodel import select
from sqlmodel import Session

from aero.database import get_session
from aero.models.data import Data
from aero.models.data_version import DataVersion

from aero import GLOBUS_CLIENT

router = APIRouter(
    prefix="/data",
    tags=["data"],
    dependencies=[],
    responses={404: {"description": "Not found"}},
)


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


@router.get("/{id}/latest", response_model=DataVersion)
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
