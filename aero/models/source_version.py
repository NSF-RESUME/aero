import datetime

from sqlalchemy import Column, Integer, String, DateTime
from aero.app import db


class SourceVersion(db.Model):
    id = Column(Integer, primary_key=True)
    version = Column(Integer)
    checksum = Column(String)
    created_at = Column(DateTime)
    source_id = Column(Integer, db.ForeignKey("source.id"))
    source = db.relationship("Source", back_populates="versions", uselist=False)
    # proxy = db.relationship("Proxy", back_populates="source_version", uselist=False)
    source_file = db.relationship(
        "SourceFile", back_populates="source_version", uselist=False
    )
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
        return "<SourceVersion(id={}, version={}, source_id={}, checksum={}, source_file={})>".format(
            self.id, self.version, self.source_id, self.checksum, self.source_file
        )

    def _set_defaults(self, **kwargs):
        if "created_at" not in kwargs:
            kwargs["created_at"] = datetime.datetime.now()
        return kwargs

    def toJSON(self):
        return {
            "id": self.id,
            "source": self.source.toJSON(),
            "version": self.version,
            "created_at": self.created_at,
            "checksum": self.checksum,
            "source_file": self.source_file.toJSON()
            if self.source_file is not None
            else None,
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
