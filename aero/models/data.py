from uuid import uuid4
from datetime import datetime

from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Uuid

from aero.app import db
from aero.app.utils import get_search_client

from aero.models.flows import Flow
from aero.models.data_file import DataFile
from aero.models.tag import DataTagTable
from aero.models.tag import Tag
from aero.models.data_version import DataVersion


class Data(db.Model):
    """All file-related metadata.

    This class contains metadata information on where data is
    stored within the user-provided Globus Connect Server.
    our
    """

    id = Column(Uuid, default=uuid4, index=True, primary_key=True)
    name = Column(String)
    url = Column(String)
    collection_uuid = Column(String)
    collection_url = Column(String)
    description = Column(String)
    # Ensure to delete timer_job_id when either `verifier` or `modifier` is altered
    versions = db.relationship(
        "DataVersion",
        back_populates="data",
        order_by="DataVersion.version",
        lazy=False,
    )
    tags = db.relationship("Tag", secondary=DataTagTable, back_populates="data")
    # outputs       = db.relationship("Output", back_populates="source")

    # TODO: Validate duplicate source links and everything else
    def __init__(
        self,
        name: str,
        collection_uuid: str,
        collection_url: str,  # maybe remove in favour of just querying globus
        description: str,
        url: str | None = None,
        tags: list[Tag] = [],
    ):
        self.name = name
        self.url = url
        self.collection_uuid = collection_uuid
        self.collection_url = collection_url
        self.description = description
        self.tags = tags

        # create
        super().__init__(
            name=self.name,
            url=url,
            collection_uuid=self.collection_uuid,
            collection_url=self.collection_url,
            description=self.description,
            tags=self.tags,
        )

        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return (
            f"<Data(id={str(self.id)}, "
            f"name={self.name}, "
            f"url={self.url}, "
            f"collection_uuid={self.collection_uuid}, "
            f"collection_url={self.collection_url}, "
            f"description={self.description})>"
        )

    # TODO: Should send hash_id instead of id
    def toJSON(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "url": self.url,
            "collection_uuid": self.collection_uuid,
            "collection_url": self.collection_url,
            "description": self.description,
            "available_versions": len(self.versions),
        }

    def add_new_version(
        self,
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

        db.session.add(new_version)
        db.session.commit()

        return get_search_client().add_entry(data_version=new_version)

    def rerun_flow(self) -> int:
        # TODO: Fix implementation
        provenances = Flow.query.filter(Flow.derived_from.any(Data.id == self.id))

        policies = []
        for prov in provenances:
            policies.append(prov._run_flow())
        return policies

    def last_version(self) -> int | DataVersion:
        try:
            l_version = self.versions[len(self.versions) - 1]
            return l_version
        except IndexError:
            return 0

    # TODO: remove ?
    # def timer_readable(self):
    #     if not (self.timer):
    #         return None

    #     return str(datetime.timedelta(seconds=self.timer))
