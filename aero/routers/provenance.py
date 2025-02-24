from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query

from pydantic import BaseModel

from sqlmodel import select
from sqlmodel import Session

from aero.database import get_session

from aero.models.data import Data
from aero.models.data_version import DataVersion
from aero.models.provenance import Provenance


router = APIRouter(
    prefix="/prov",
    tags=["provenance"],
    dependencies=[],
    responses={404: {"description": "Not found"}},
)


class ProvRecord(BaseModel):
    input_data: dict
    output_data: dict
    flow_id: UUID


@router.get("/", response_model=list[Provenance])
# @authenticated
def list_prov(
    offset: int = 0,
    limit: int = Query(default=15, le=15),
    session: Session = Depends(get_session),
):
    provs = session.exec(
        select(Provenance).order_by(Provenance.id.desc()).offset(offset).limit(limit)
    ).all()
    return provs


@router.post("/new", response_model=Provenance)
# @authenticated
def add_record(pr: ProvRecord, session: Session = Depends(get_session)):
    try:
        input_versions = [
            session.exec(
                select(DataVersion).where(
                    DataVersion.data_id == i["id"],
                    DataVersion.version == i["version"],
                )
            ).first()
            for i in pr.input_data.values()
        ]
        # create new versions for output data
        output_versions = []
        for o in pr.output_data.values():
            d = session.exec(select(Data).where(Data.id == o.id)).first()
            d.add_new_version(
                new_file=o["file_bn"],
                format=o["file_format"],
                checksum=o["checksum"],
                size=o["size"],
                created_at=o["created_at"],
                encoding=o.get("encoding", "utf-8"),
            )

            # TODO: maybe fix
            d.rerun_flow()
            output_versions.append(d.last_version())

        p = Provenance(
            flow_id=pr.flow_id,
            contributed_to=output_versions,
            derived_from=input_versions,
        )

        session.add(p)
        session.commit()
        session.refresh(p)
        return p
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
