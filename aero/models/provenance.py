from typing import TYPE_CHECKING
from typing import Optional
from uuid import UUID
from uuid import uuid4
from sqlmodel import Field
from sqlmodel import Relationship
from sqlmodel import Session
from sqlmodel import SQLModel


if TYPE_CHECKING:  # pragma: nocover
    from aero.models.data_version import DataVersion


class ProvenanceDerivation(SQLModel, table=True):
    __tablename__ = "provenancederivation"
    prov_id: Optional[UUID] = Field(
        default=None, foreign_key="provenance.id", primary_key=True
    )
    derived_version_id: Optional[UUID] = Field(
        default=None, foreign_key="dataversion.id", primary_key=True
    )


class ProvenanceContribution(SQLModel, table=True):
    __tablename__ = "provenancecontribution"
    prov_id: Optional[UUID] = Field(
        default=None, foreign_key="provenance.id", primary_key=True
    )
    produced_version_id: Optional[UUID] = Field(
        default=None, foreign_key="dataversion.id", primary_key=True
    )


class Provenance(SQLModel, table=True):
    __tablename__ = "provenance"
    id: UUID = Field(default_factory=uuid4, index=True, primary_key=True)
    flow_id: UUID = Field(foreign_key="flow.id")
    derived_from: list["DataVersion"] = Relationship(
        link_model=ProvenanceDerivation,
        back_populates="provenance_source",
    )
    contributed_to: list["DataVersion"] = Relationship(
        link_model=ProvenanceContribution,
        back_populates="provenance_contribution",
    )


def create_provenance(
    session: Session,
    flow_id: uuid4,
    derived_from: list["DataVersion"] = [],
    contributed_to: list["DataVersion"] = [],
) -> Provenance:
    p = Provenance(
        flow_id=flow_id, derived_from=derived_from, contributed_to=contributed_to
    )

    session.add(p)
    session.commit()
    session.refresh(p)

    return p
