from datetime import datetime
from uuid import UUID
from uuid import uuid4
from typing import TYPE_CHECKING
from typing import Optional

from sqlmodel import Field
from sqlmodel import Relationship
from sqlmodel import Session
from sqlmodel import SQLModel

from aero.models.data_file import DataFile
from aero.models.provenance import ProvenanceContribution
from aero.models.provenance import ProvenanceDerivation

if TYPE_CHECKING:
    from aero.models.data import Data
    from aero.models.provenance import Provenance


class DataVersion(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, index=True, primary_key=True)
    version: int | None = Field(default=None, index=True)
    checksum: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.now)
    data_id: Optional[UUID] = Field(
        default=None, foreign_key="data.id", primary_key=True
    )  # Column(Uuid, db.ForeignKey("data.id"))
    data: Optional["Data"] = Relationship(back_populates="versions")
    data_file: Optional["DataFile"] = Relationship(back_populates="version")
    provenance_contribution: Optional["Provenance"] = Relationship(
        link_model=ProvenanceContribution, back_populates="contributed_to"
    )
    provenance_source: Optional["Provenance"] = Relationship(
        link_model=ProvenanceDerivation, back_populates="derived_from"
    )


def create_dataversion(
    session: Session,
    version: int,
    checksum: str,
    data_id: UUID,
) -> DataVersion:
    v = DataVersion(
        version=version,
        checksum=checksum,
        data_id=data_id,
    )

    session.add(v)
    session.commit()
    session.refresh(v)

    return v
