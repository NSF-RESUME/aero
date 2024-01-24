from sqlalchemy import Column, Integer, String, Numeric, ForeignKey
from sqlalchemy.orm import relationship

from pathlib import Path
from osprey.worker.models.utils import SOURCE_DIR
from osprey.worker.models.utils import TEMP_DIR
from osprey.worker.models.database import Base


# Assume that this is sa read-only class
class SourceFile(Base):
    __tablename__ = "source_file"
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True)
    file_name = Column(String)
    file_type = Column(String)
    size = Column(Numeric)
    source_version_id = Column(Integer, ForeignKey("source_version.id"))
    encoding = Column(String)
    source_version = relationship(
        "SourceVersion", back_populates="source_file", uselist=False
    )

    def __init__(self, **kwargs):
        kwargs = self._write_file(**kwargs)
        super().__init__(**kwargs)

    def _write_file(self, file_name: str, file_type: str, **kwargs) -> dict:
        """_summary_

        Args:
            file_name (str): Path to the temporary path that needs to be committed
            file_type (str): File extension
        Returns:
            dict: updated kwargs initially passed to the function
        """
        _ = kwargs["args"]
        basename = file_name

        SOURCE_DIR.mkdir(
            parents=True, exist_ok=True
        )  # TODO remove from here so it only executes once
        fn = SOURCE_DIR / basename
        Path(TEMP_DIR, file_name).rename(fn)

        kwargs["file_name"] = basename
        kwargs["file_type"] = file_type
        kwargs["size"] = fn.stat.st_size
        kwargs.pop("args")
        return kwargs

    def __repr__(self) -> str:
        return f"SourceFile(id={self.id}, file_name={self.file_name}, encoding={self.encoding}, file_size={self.size}, source_version_id={self.source_version_id})"

    @property
    def file(self):
        pass


"""

NOTE: This class is duplicated from the `class SourceFile` from

    /osprey/server/models/source_file.py

But the usecase is, to separates the representation for different microservices

"""
