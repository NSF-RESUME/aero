from uuid import UUID
from uuid import uuid4
from typing import TYPE_CHECKING

from sqlmodel import Field
from sqlmodel import Relationship
from sqlmodel import Session
from sqlmodel import SQLModel

if TYPE_CHECKING:
    from aero.models.flows import Flow


class Function(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    flows: list["Flow"] = Relationship(back_populates="function")


def create_function(
    session: Session, uuid: uuid4, flows: list["Flow"] = []
) -> Function:
    f = Function(id=uuid, flows=flows)

    session.add(f)
    session.commit()
    session.refresh(f)

    return f
