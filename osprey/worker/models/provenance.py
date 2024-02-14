from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Table

from sqlalchemy.orm import relationship

from osprey.worker.models.database import Base
from osprey.worker.models.database import Session


provenance_derivation = Table(
    "provenance_derivation",
    Column("provenance_id", Integer, ForeignKey("provenance.id")),
    Column("previous_source_version_id", Integer, ForeignKey("source_version.id")),
)


class Provenance(Base):
    id = Column(Integer, primary_key=True)
    function_id = Column(Integer, ForeignKey("function.id"))
    function_args = Column(String)
    description = Column(String)
    timer = Column(Integer)
    timer_job_id = Column(String)
    derived_from = relationship(
        "SourceVersion",
        secondary=provenance_derivation,
        backref="source_versions",
        uselist=True,
    )
    contributed_to = relationship("Output", backref="output", lazy=True)

    def __init__(
        self,
        function_id: str,
        derived_from: list,
        contributed_to: list,
        description: str = "",
        function_args: str = "",
        timer: int | None = None,
    ):
        with Session() as session:
            session.add(self)
            session.commit()

        if timer is None:
            timer = 86400  # run daily

        super().__init__(
            function_id=function_id,
            derived_from=derived_from,
            contributed_to=contributed_to,
            description=description,
            function_args=function_args,
            timer=timer,
        )

    def __repr__(self):
        return "<Provenance(id={}, derived_from={}, contributed_to={}, function_id='{}', function_args='{}', timer='{}', 'timer_job_id='{}')>".format(
            self.id,
            self.derived_from,
            self.contributed_to,
            self.description,
            self.function_id,
            self.timer,
            self.timer_job_id,
        )
