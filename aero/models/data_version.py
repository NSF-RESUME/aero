import datetime

from uuid import uuid4

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Uuid
from aero.app import db


class DataVersion(db.Model):
    id = Column(Uuid, default=uuid4, index=True, primary_key=True)
    version = Column(Integer)
    checksum = Column(String)
    created_at = Column(DateTime)
    data_id = Column(Uuid, db.ForeignKey("data.id"))
    data = db.relationship("Data", back_populates="versions", uselist=False)
    # proxy = db.relationship("Proxy", back_populates="source_version", uselist=False)
    data_file = db.relationship("DataFile", back_populates="version", uselist=False)
    # provenance    = db.relationship("Provenance", back_populates='source_version', uselist=False)
    # contributed_to= db.relationship("Provenance", secondary=provenance_derivation, back_populates='outputs')

    # TODO: Make sure to have created_at as current time if it is not passed as an argument
    # NOTE: Also create a proxy automatically ig?

    # def __init__(self, *args, **kwargs):
    #     1. Set current_time if None
    #     2. super()

    def __init__(self, **kwargs):
        kwargs = self._set_defaults(**kwargs)
        super().__init__(**kwargs)
        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return "<DataVersion(id={}, version={}, data_id={}, checksum={}, data_file={})>".format(
            self.id, self.version, self.data_id, self.checksum, self.data_file
        )

    def _set_defaults(self, **kwargs):
        if "created_at" not in kwargs or kwargs["created_at"] is None:
            kwargs["created_at"] = datetime.datetime.now()
        return kwargs

    def toJSON(self):
        return {
            "id": self.id,
            "data": self.data.toJSON(),
            "version": self.version,
            "created_at": str(self.created_at),
            "checksum": self.checksum,
            "data_file": (
                self.data_file.toJSON() if self.data_file is not None else None
            ),
        }

    # def create_proxy(self, replace=False):
    #     if self.proxy is not None and not replace:
    #         return self.proxy

    #     # TODO: Need to create representation
    #     proxy = Proxy(source_version=self)
    #     try:
    #         db.session.add(proxy)
    #         db.session.commit()
    #     except SQLAlchemyError:
    #         raise
    #     return proxy
