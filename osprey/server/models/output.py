import hashlib

from pathlib import Path

from sqlalchemy import Column, Integer, String

from osprey.server.app import db
from osprey.server.models.output_version import OutputVersion

# TODO: Place in better location
GCS_OUTPUT_DIR = Path("/dsaas_storage/output")


class Output(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String)
    provenance_id = db.Column(db.Integer, db.ForeignKey("provenance.id"))
    output_versions = db.relationship(
        "OutputVersion",
        backref="output_version",
        order_by="OutputVersion.version",
        lazy=True,
    )

    def add_new_version(self, filename: str):
        # get current checksum
        with open(Path(GCS_OUTPUT_DIR, filename), "r") as f:
            checksum = hashlib.md5(f.read().encode("utf-8")).hexdigest()

        num_version = 0

        if self.output_versions is not None:
            num_version = len(self.output_versions)

            if num_version > 0:
                last_version = self.output_versions[num_version - 1]

                # compare checksums
                with open(Path(GCS_OUTPUT_DIR, last_version.filename), "r") as f:
                    prev_checksum = hashlib.md5(f.read().encode("utf-8")).hexdigest()

                if prev_checksum == checksum:
                    return

        v = OutputVersion(
            filename=filename,
            version=num_version + 1,
            checksum=checksum,
            source_id=self.id,
        )
        db.session.add(v)
        db.session.commit()

    def __repr__(self):
        return f"<Output(id={self.id}, name={self.name}, provenance_id={self.provenance_id}, versions={self.output_versions})>"

    def toJSON(self):
        return {
            "id": self.id,
            "name": self.name,
            "provenance_id": self.provenance_id,
            "versions": [v.toJSON() for v in self.output_versions]
            if self.output_versions is not None
            else None,
        }
