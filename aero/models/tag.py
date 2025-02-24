from uuid import UUID
from typing import TYPE_CHECKING
from typing import Optional

from sqlmodel import Field
from sqlmodel import Relationship
from sqlmodel import SQLModel

if TYPE_CHECKING:
    from aero.models.data import Data


class DataTagTable(SQLModel, table=True):
    # id: int | None = Field(default=None, primary_key=True)
    data_id: Optional[UUID] = Field(
        default=None, foreign_key="data.id", primary_key=True
    )
    tag_id: Optional[int] = Field(default=None, foreign_key="tag.id", primary_key=True)


class Tag(SQLModel, table=True):
    id: int | None = Field(
        default=None, primary_key=True
    )  # Column(Integer, primary_key=True)
    name: str  # = Field(nullable=False, index=True)  # Column(String)
    data: list["Data"] = Relationship(link_model=DataTagTable, back_populates="tags")
