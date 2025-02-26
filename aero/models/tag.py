from uuid import UUID
from typing import TYPE_CHECKING
from typing import Optional

from sqlmodel import Field
from sqlmodel import Relationship
from sqlmodel import SQLModel
from sqlmodel import Session


if TYPE_CHECKING:  # pragma: nocover
    from aero.models.data import Data


class DataTagTable(SQLModel, table=True):
    __tablename__ = "datatagtable"
    data_id: Optional[UUID] = Field(
        default=None, foreign_key="data.id", primary_key=True
    )
    tag_id: Optional[int] = Field(default=None, foreign_key="tag.id", primary_key=True)


class Tag(SQLModel, table=True):
    __tablename__ = "tag"
    id: int | None = Field(
        default=None, primary_key=True
    )  # Column(Integer, primary_key=True)
    name: str  # = Field(nullable=False, index=True)  # Column(String)
    data: list["Data"] = Relationship(link_model=DataTagTable, back_populates="tags")


def create_tag(session: Session, name: str) -> Tag:
    tag = Tag(name=name)

    session.add(tag)
    session.commit()
    session.refresh(tag)

    return tag
