from uuid import UUID
from uuid import uuid4

from typing import TYPE_CHECKING
from typing import Optional

from sqlmodel import Field
from sqlmodel import Session
from sqlmodel import SQLModel
from sqlmodel import Relationship


if TYPE_CHECKING:  # pragma: nocover
    from aero.models.data_version import DataVersion


class DataFile(SQLModel, table=True):
    __tablename__ = "datafile"
    id: UUID = Field(
        default_factory=uuid4, primary_key=True, index=True
    )  # Column(Uuid, default=uuid4, index=True, primary_key=True)
    file_name: str = Field(nullable=False)  # Column(String)
    file_type: str | None = Field(default=None)  # Column(String)
    size: float = Field(nullable=False)  # Column(Numeric)
    encoding: str = Field(default="utf-8")  # Column(String)
    version_id: UUID = Field(
        foreign_key="dataversion.id", primary_key=True
    )  # Column(Uuid, db.ForeignKey("data_version.id"))
    version: Optional["DataVersion"] = Relationship(back_populates="data_file")


def create_datafile(
    session: Session,
    file_name: str,
    size: float,
    version_id: uuid4,
    file_type: str | None = None,
    encoding: str | None = None,
) -> DataFile:
    df = DataFile(
        file_name=file_name,
        size=size,
        version_id=version_id,
        file_type=file_type,
        encoding=encoding,
    )

    session.add(df)
    session.commit()
    session.refresh(df)

    return df
