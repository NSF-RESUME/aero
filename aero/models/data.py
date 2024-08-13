import datetime

from uuid import uuid4

from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Uuid

from aero.app import db
from aero.app.utils import get_search_client
from aero.globus.error import FLOW_TIMER_ERROR
from aero.globus.error import MODEL_INSUFFICIENT_ATTRS
from aero.globus.error import ServiceError

import aero.automate.timer as globus_timer
from aero.models.flows import Flow
from aero.models.data_file import DataFile
from aero.models.tag import DataTagTable
from aero.models.tag import Tag
from aero.models.data_version import DataVersion
from aero.globus.flow import get_job
from aero.globus.utils import FlowEnum
from aero.config import Config


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
    timer = Column(Integer)  # in seconds
    vm_func = Column(String)
    email = Column(String)
    # Ensure to delete timer_job_id when either `verifier` or `modifier` is altered
    user_endpoint = Column(String)
    timer_job_id = Column(String)
    provenance_job_id = Column(String)
    flow_kind = Column(Integer)
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
        timer: int | None = None,
        vm_func: str | None = None,
        email: str | None = None,
        user_endpoint: str | None = None,
        timer_job_id: str | None = None,
        provenance_job_id: int | None = None,
        flow_kind: int | None = None,
        tags: list[Tag] = [],
    ):
        self.name = name
        self.url = url
        self.collection_uuid = collection_uuid
        self.collection_url = collection_url
        self.description = description
        self.vm_func = vm_func
        self.email = email
        self.timer_job_id = timer_job_id
        self.provenance_job_id = provenance_job_id
        self.tags = tags

        if timer is None:
            self.timer = 86400  # 1 day

        if vm_func is not None and user_endpoint is None:
            raise ServiceError(
                code=MODEL_INSUFFICIENT_ATTRS,
                message="vm_func needs a user_endpoint to be executed on",
            )

        if flow_kind is None:
            if vm_func is not None:
                self.flow_kind = FlowEnum.VERIFY_AND_MODIFY
            else:
                self.flow_kind = FlowEnum.NONE
        else:
            self.flow_kind = flow_kind

        # TODO: don't set it to anything
        if user_endpoint is None:
            self.user_endpoint = Config.GLOBUS_WORKER_UUID

        # create
        super().__init__(
            name=self.name,
            url=self.url,
            collection_uuid=self.collection_uuid,
            collection_url=self.collection_url,
            description=self.description,
            timer=self.timer,
            vm_func=self.vm_func,
            email=self.email,
            user_endpoint=self.user_endpoint,
            timer_job_id=self.timer_job_id,
            provenance_job_id=self.provenance_job_id,
            flow_kind=self.flow_kind,
            tags=self.tags,
        )

        db.session.add(self)
        db.session.commit()

        # after_create
        self._start_timer_flow()

    def __repr__(self):
        return (
            f"<Data(id={self.id}, "
            f"name={self.name}, "
            f"url={self.url}, "
            f"collection_uuid={self.collection_uuid}, "
            f"collection_url={self.collection_url}, "
            f"description={self.description})>"
        )

    # TODO: Should send hash_id instead of id
    def toJSON(self):
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "collection_uuid": self.collection_uuid,
            "collection_url": self.collection_url,
            "user_endpoint": self.user_endpoint,
            "description": self.description,
            "timer": self.timer,
            "vm_func": self.vm_func,
            "email": self.email,
            "available_versions": len(self.versions),
        }

    def add_new_version(
        self,
        new_file: str,
        format: str,
        checksum: str,
        size: int,
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

        return get_search_client().add_entry(source_version=new_version)

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
    def timer_readable(self):
        if not (self.timer):
            return None

        return str(datetime.timedelta(seconds=self.timer))

    def _start_timer_flow(self, flush=False):
        if not flush and self.timer_job_id is not None:
            raise ServiceError(FLOW_TIMER_ERROR, "source already has a flow timer")

        self.timer_job_id = globus_timer.set_timer(
            self.timer,
            self.id,
            self.email,
            self.flow_kind,
            user_endpoint=self.user_endpoint,
        )
        db.session.add(self)
        db.session.commit()

    def get_timer_job(self):
        return get_job(self.timer_job_id)

    def last_refreshed_at(self):
        timer_job = self.get_timer_job()
        if timer_job is None:
            return
        return timer_job.get("last_ran_at")

    # TODO: Assuming the users are giving function UUID for now, and not getting us to register
    # NOTE: If they are registering their own functions, then they have to make sure to give our group access
    # Hence we need have a separate routes for the to register functions or we enable `client.py` to hold the group_id, and hope the group_id does not change
