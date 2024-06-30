import datetime
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String

from osprey.server.app import db
from osprey.server.app.utils import search_client
from osprey.server.lib.error import (
    ServiceError,
    MODEL_INSUFFICIENT_ATTRS,
    FLOW_TIMER_ERROR,
)
from osprey.server.models.provenance import Provenance
from osprey.server.models.source_file import SourceFile
from osprey.server.models.tag import SourceTagTable
from osprey.server.models.source_version import SourceVersion
from osprey.server.jobs.timer import set_timer
from osprey.server.lib.globus_flow import get_job, FlowEnum, FLOW_IDS
from osprey.server.config import Config


class Source(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String)
    url = Column(String)
    collection_uuid = Column(String)
    collection_url = Column(String)
    description = Column(String)
    timer = Column(Integer)  # in seconds
    verifier = Column(String)
    modifier = Column(String)
    email = Column(String)
    # Ensure to delete timer_job_id when either `verifier` or `modifier` is altered
    user_endpoint = Column(String)
    timer_job_id = Column(String)
    flow_kind = Column(Integer)
    versions = db.relationship(
        "SourceVersion",
        back_populates="source",
        order_by="SourceVersion.version",
        lazy=False,
    )
    tags = db.relationship("Tag", secondary=SourceTagTable, back_populates="sources")
    # outputs       = db.relationship("Output", back_populates="source")

    # TODO: Validate duplicate source links and everything else
    def __init__(self, **kwargs):
        # validate
        kwargs = self._set_defaults(**kwargs)
        self._validate(**kwargs)

        # create
        super().__init__(**kwargs)
        db.session.add(self)
        db.session.commit()

        # after_create
        self._start_timer_flow()

    def __repr__(self):
        return (
            f"<Source(id={self.id}, "
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
            "description": self.description,
            "timer": self.timer,
            "verifier": self.verifier,
            "modifier": self.modifier,
            "email": self.email,
            "available_versions": len(self.versions),
        }

    def add_new_version(
        self, new_file: str, format: str, checksum: str, size: int
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
            return

        new_version = SourceVersion(
            version=version_number,
            source_id=self.id,
            checksum=checksum,
        )

        new_version.source_file = SourceFile(
            encoding="utf-8",
            file_type=format,
            file_name=new_file,
            size=size,
            source_version_id=version_number,
        )

        db.session.add(new_version)
        db.session.commit()

        return search_client.add_entry(source_version=new_version)

    def rerun_flow(self) -> int:
        # TODO: Fix implementation
        provenances = Provenance.query.filter(
            Provenance.derived_from.any(Source.id == self.id)
        )

        policies = []
        for prov in provenances:
            policies.append(prov._run_flow())
        return policies

    def last_version(self) -> int | SourceVersion:
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

    def _validate(self, **kwargs):
        for attr in ["name", "url", "timer"]:  # Required attributes
            if attr not in kwargs.keys():
                raise ServiceError(
                    code=MODEL_INSUFFICIENT_ATTRS,
                    message="Name, url and timer values are required",
                )

    def _set_defaults(self, **kwargs):
        if "timer" not in kwargs:
            kwargs["timer"] = 86400  # 1 day
        if "flow_kind" not in kwargs:
            if (
                kwargs.get("verifier") is not None
                and kwargs.get("modifier") is not None
            ):
                kwargs["flow_kind"] = FlowEnum.VERIFY_AND_MODIFY
            elif (
                kwargs.get("verifier") is not None or kwargs.get("modifier") is not None
            ):
                kwargs["flow_kind"] = FlowEnum.VERIFY_OR_MODIFY
            else:
                kwargs["flow_kind"] = FlowEnum.NONE

        if "user_endpoint" not in kwargs:
            kwargs["user_endpoint"] = Config.GLOBUS_WORKER_UUID

        return kwargs

    def _start_timer_flow(self, flush=False):
        if not flush and self.timer_job_id is not None:
            raise ServiceError(FLOW_TIMER_ERROR, "source already has a flow timer")

        self.timer_job_id = set_timer(
            self.timer,
            self.id,
            self.email,
            self.flow_kind,
            user_endpoint=self.user_endpoint,
        )
        db.session.add(self)
        db.session.commit()

    def get_timer_job(self):
        return get_job(FLOW_IDS[self.flow_kind], self.timer_job_id)

    def last_refreshed_at(self):
        timer_job = self.get_timer_job()
        if timer_job is None:
            return
        return timer_job.get("last_ran_at")

    # TODO: Assuming the users are giving function UUID for now, and not getting us to register
    # NOTE: If they are registering their own functions, then they have to make sure to give our group access
    # Hence we need have a separate routes for the to register functions or we enable `client.py` to hold the group_id, and hope the group_id does not change
