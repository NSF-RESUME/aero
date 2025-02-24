from uuid import UUID
from uuid import uuid4
from datetime import datetime

from typing import TYPE_CHECKING
from typing import Optional

from sqlmodel import Field
from sqlmodel import Relationship
from sqlmodel import Session
from sqlmodel import SQLModel
from sqlmodel import select

from aero.utils import get_search_client
from aero.models.tag import DataTagTable

if TYPE_CHECKING:
    from aero.models.flows import Flow
    from aero.models.data_file import DataFile
    from aero.models.tag import Tag
    from aero.models.data_version import DataVersion


class Data(SQLModel, table=True):
    """All file-related metadata.

    This class contains metadata information on where data is
    stored within the user-provided Globus Connect Server.
    our
    """

    id: UUID = Field(
        default_factory=uuid4, index=True, primary_key=True
    )  # Column(Uuid, default=uuid4, index=True, primary_key=True)
    name: str  # = Field(nullable=False)  # Column(String)
    url: str | None = Field(default=None)  # Column(String)
    collection_uuid: UUID | None = Field(default=None)  # Column(String)
    collection_url: str | None = Field(default=None)  # Column(String)
    description: str | None = Field(default=None)  # Column(String)
    # Ensure to delete timer_job_id when either `verifier` or `modifier` is altered
    versions: list["DataVersion"] = Relationship(
        back_populates="data",
    )
    tags: list["Tag"] = Relationship(link_model=DataTagTable, back_populates="data")

    def add_new_version(
        self,
        session: Session,
        new_file: str,
        format: str,
        checksum: str,
        size: int,
        created_at: datetime | None = None,
        encoding: str = "utf-8",
    ) -> str:
        """Commit data to the database.

        Args:
            new_file (str): File path to the temporarily stored data.
            format (str): The extension of the file.
        """
        if self.last_version() == 0:
            version_number = 1
        else:
            version_number = self.last_version().version + 1

        # compare checksums to see if new version
        try:
            old_checksum = self.last_version().checksum
        except Exception:  # if source_file doesn't exist
            old_checksum = None

        if old_checksum == checksum:
            return {"code": 201, "message": "Version already exists"}

        new_version = DataVersion(
            version=version_number,
            data_id=self.id,
            checksum=checksum,
            created_at=created_at,
        )

        new_version.data_file = DataFile(
            encoding=encoding,
            file_type=format,
            file_name=new_file,
            size=size,
            version_id=new_version.id,
        )

        session.add(new_version)
        session.commit()
        session.refresh(new_version)

        return get_search_client().add_entry(data_version=new_version)

    def rerun_flow(self, session: Session) -> int:
        # TODO: Fix implementation
        statement = select(Flow).where(
            any([d.id == self.id for d in Flow.derived_from])
        )
        provenances = session.exec(statement).all()

        policies = []
        for prov in provenances:
            policies.append(prov._run_flow(session=session))
        return policies

    def last_version(self) -> Optional["DataVersion"]:
        try:
            l_version = self.versions[len(self.versions) - 1]
            return l_version
        except IndexError:
            return None


def create_data(
    session: Session,
    name: str,
    url: str | None = None,
    collection_uuid: str | None = None,
    collection_url: str | None = None,
    description: str | None = None,
    tags: list["Tag"] = [],
) -> Data:
    d = Data(
        name=name,
        url=url,
        collection_uuid=collection_uuid,
        collection_url=collection_url,
        description=description,
        tags=tags,
    )

    session.add(d)
    session.commit()
    session.refresh(d)

    return d
