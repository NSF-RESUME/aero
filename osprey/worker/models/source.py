import datetime
import hashlib
import requests
import uuid

from mimetypes import guess_extension
from pathlib import Path

from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String
from osprey.worker.models.database import Base
from osprey.worker.models.database import Session
from osprey.worker.models.database import search_client
# from osprey.worker.jobs.verifier   import verifier_microservice

from osprey.worker.models.source_version import SourceVersion
from osprey.worker.models.source_file import SourceFile
from osprey.worker.models.utils import TEMP_DIR
from osprey.worker.models.utils import SOURCE_DIR


# Assume that this is sa read-only class
class Source(Base):
    __tablename__ = "source"
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True)
    name = Column(String)
    url = Column(String)
    description = Column(String)
    timer = Column(Integer)  # in seconds
    verifier = Column(String)
    modifier = Column(String)
    email = Column(String)
    user_endpoint = Column(String)
    timer_job_id = Column(String)
    flow_kind = Column(Integer)
    versions = relationship(
        "SourceVersion",
        back_populates="source",
        order_by="SourceVersion.version",
        lazy=False,
    )

    def __repr__(self):
        return f"Source(id={self.id}, name={self.name}, url={self.url}, email={self.email}, timer={self.timer_readable()})"

    def add_new_version(self, new_file: str, format: str) -> None:
        """Commit data to the database and store in GCS server.

        Args:
            new_file (str): File path to the temporarily stored data.
            format (str): The extension of the file.
        """
        with Session() as session:
            version_number = self.last_version().version + 1

            # compare checksums to see if new version
            try:
                with open(
                    Path(SOURCE_DIR, self.last_version().source_file.file_name), "r"
                ) as f:
                    old_checksum = hashlib.md5(f.read().encode("utf-8")).hexdigest()
            except Exception:  # if source_file doesn't exist
                old_checksum = None

            with open(Path(TEMP_DIR, new_file), "r") as f:
                new_checksum = hashlib.md5(f.read().encode("utf-8")).hexdigest()

            if old_checksum == new_checksum:
                return

            new_version = SourceVersion(
                version=version_number, source_id=self.id, checksum=new_checksum
            )

            new_version.source_file = SourceFile(
                encoding="utf-8",
                file_type=format,
                file_name=new_file,
                args={"version": version_number, "source_id": self.id},
            )
            session.add(new_version)
            session.commit()

            search_client.add_entry(source_version=new_version)

    def download(self) -> tuple[str, str]:
        """Download data from user-specified repository.

        Returns:
            tuple[str, str]: Path to the data and its
                associated extension.
        """
        response = requests.get(self.url)
        content_type = response.headers["content-type"]
        ext = guess_extension(content_type.split(";")[0])

        bn = str(uuid.uuid4())
        fn = Path(TEMP_DIR, bn)

        TEMP_DIR.mkdir(exist_ok=True)

        with open(fn, "w+") as f:
            f.write(response.content.decode("utf-8"))

        return bn, ext

    def last_version(self):
        try:
            l_version = self.versions[len(self.versions) - 1]
            return l_version
        except IndexError:
            return 0

    def timer_readable(self):
        if not (self.timer):
            return None

        return str(datetime.timedelta(seconds=self.timer))

    @classmethod
    def get(cls, source_id):
        with Session() as session:
            source = session.query(Source).get(source_id)
        return source

    # @classmethod
    # def nearest_refresh(cls):       # Assume that it runs every 5 mins
    #     with Session() as s:
    #         return s.query(cls).count()


"""

NOTE: This class is duplicated from the `class Source` from

    /osprey/server/models/source.py

But the usecase is, to separates the representation for different microservices

"""
