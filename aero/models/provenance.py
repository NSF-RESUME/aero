from sqlalchemy import Column
from sqlalchemy import Uuid
from uuid import uuid4

from aero.app import db
from aero.models.data_version import DataVersion

provenance_derivation = db.Table(
    "provenance_derivation",
    Column("prov_id", Uuid, db.ForeignKey("provenance.id")),
    Column("derived_version_id", Uuid, db.ForeignKey("data_version.id")),
)

provenance_contribution = db.Table(
    "provenance_contribution",
    Column("prov_id", Uuid, db.ForeignKey("provenance.id")),
    Column("produced_version_id", Uuid, db.ForeignKey("data_version.id")),
)


class Provenance(db.Model):
    id = Column(Uuid, default=uuid4, index=True, primary_key=True)
    flow_id = Column(Uuid)
    derived_from = db.relationship(
        "DataVersion",
        secondary=provenance_derivation,
        backref="provenance_contribution",
        uselist=True,
    )
    contributed_to = db.relationship(
        "DataVersion",
        secondary=provenance_contribution,
        backref="provenance_source",
        lazy=True,
    )

    def __init__(
        self,
        flow_id: uuid4,
        derived_from: list[DataVersion],
        contributed_to: list[DataVersion],
    ):
        super().__init__(
            flow_id=flow_id, derived_from=derived_from, contributed_to=contributed_to
        )

        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return (
            f"<Provenance(id={self.id}, "
            f"flow_id={self.flow_id}, "
            f"contributed_to={', '.join(c for c in self.contributed_to)}, "
            f"derived_from={', '.join(d for d in self.derived_from)})>"
        )

    def toJSON(self):
        return {
            "id": self.id,
            "flow_id": self.flow_id,
            "contributed_to": [c.toJSON() for c in self.contributed_to],
            "derived_from": [d.toJSON() for d in self.derived_from],
        }
