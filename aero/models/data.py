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

from aero.models.tag import DataTagTable

from aero.models.data_version import DataVersion
from aero.models.data_file import DataFile

from aero.models.flows import Flow

from aero.models.source_type import SourceType
from aero.models.source_type import SourceUrl

from aero import GLOBUS_CLIENT

if TYPE_CHECKING:
    from aero.models.tag import Tag  # pragma: nocover


class Data(SQLModel, table=True):
    """All file-related metadata.

    This class contains metadata information on where data is
    stored within the user-provided Globus Connect Server.
    our
    """

    __tablename__ = "data"

    id: UUID = Field(
        default_factory=uuid4, index=True, primary_key=True
    )  # Column(Uuid, default=uuid4, index=True, primary_key=True)
    name: str  # = Field(nullable=False)  # Column(String)
    url: str | None = Field(default=None)  # Column(String)
    collection_uuid: UUID | None = Field(default=None)  # Column(String)
    collection_url: str | None = Field(default=None)  # Column(String)
    description: str | None = Field(default=None)  # Column(String)
    # Reference-only source: notify records a new version from the event metadata and
    # no bytes are copied into a Globus collection. Orthogonal to having a type.
    no_copy: bool = Field(default=False)
    # Ensure to delete timer_job_id when either `verifier` or `modifier` is altered
    versions: list["DataVersion"] = Relationship(
        back_populates="data",
    )
    tags: list["Tag"] = Relationship(link_model=DataTagTable, back_populates="data")
    # The FK lives on sourcetype, so this adds no column to `data`.
    source_type: Optional["SourceType"] = Relationship(back_populates="data")

    def add_new_version(
        self,
        session: Session,
        new_file: str,
        format: str,
        checksum: str,
        size: int,
        created_at: datetime | None = None,
        encoding: str = "utf-8",
        source_key: str | None = None,
        dedup: bool = True,
    ) -> str:
        """Commit data to the database.

        Args:
            new_file (str): File path to the temporarily stored data.
            format (str): The extension of the file.
            source_key (str | None): Normalized object key this version came from.
                When set, change detection compares against the last version with the
                *same* key rather than the tail of the version list — so one Data fed
                by several URLs dedups per URL. Left None the behavior is unchanged.
            dedup (bool): When False, always create a version even if the checksum
                matches. Driven by the notify payload's ``dedup`` flag.
        """
        last = self.last_version()
        version_number = 1 if last is None else last.version + 1

        # compare checksums to see if new version
        if source_key is None:
            previous = last
        else:
            previous = self._last_version_for(session, source_key)

        old_checksum = previous.checksum if previous is not None else None

        if dedup and old_checksum == checksum:
            return {"code": 201, "message": "Version already exists"}

        new_version = DataVersion(
            version=version_number,
            data_id=self.id,
            checksum=checksum,
            created_at=created_at,
            source_key=source_key,
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

        return GLOBUS_CLIENT.add_search_entry(entry=new_version._conf_search_entry())

    def rerun_flow(
        self,
        session: Session,
        trigger_url: str | None = None,
        signed_url: str | None = None,
    ) -> int:
        # TODO: Fix implementation
        statement = select(Flow).where(Flow.derived_from.any(id=self.id))
        provenances = session.exec(statement).all()

        policies = []
        for prov in provenances:
            policies.append(
                prov._run_flow(
                    session=session,
                    trigger_url=trigger_url,
                    signed_url=signed_url,
                    source_data_id=self.id,
                )
            )
        return policies

    def _last_version_for(
        self, session: Session, source_key: str
    ) -> Optional["DataVersion"]:
        """The newest version produced by one particular object key."""
        return session.exec(
            select(DataVersion)
            .where(DataVersion.data_id == self.id)
            .where(DataVersion.source_key == source_key)
            .order_by(DataVersion.version.desc())
        ).first()

    def last_version(self) -> Optional["DataVersion"]:
        # Pick by version number, not by position: `versions` comes back in whatever
        # order SQLAlchemy loaded it, which is not necessarily version order — and a
        # type accumulates versions from several URLs.
        if not self.versions:
            return None
        return max(self.versions, key=lambda v: v.version or 0)


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
