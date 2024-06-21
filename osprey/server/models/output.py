from sqlalchemy import Column, Integer, String

from osprey.server.app import db
from osprey.server.models.output_version import OutputVersion

# TODO: Place in better location
# GCS_OUTPUT_DIR = Path("/dsaas_storage/output")


class Output(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String)
    url = Column(String)
    provenance_id = db.Column(db.Integer, db.ForeignKey("provenance.id"))
    output_versions = db.relationship(
        "OutputVersion",
        back_populates="output",
        order_by="OutputVersion.version",
        lazy=True,
    )

    def __init__(self, name: str):
        super().__init__(name=name)
        db.session.add(self)
        db.session.commit()

    def add_new_version(self, filename: str, checksum: str):
        # get current checksum
        num_version = 0

        if self.output_versions is not None:
            num_version = len(self.output_versions)

            if num_version > 0:
                last_version = self.output_versions[num_version - 1]

                # compare checksums
                if last_version.checksum == checksum:
                    return

        v = OutputVersion(
            filename=filename,
            version=num_version + 1,
            checksum=checksum,
            output_id=self.id,
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
