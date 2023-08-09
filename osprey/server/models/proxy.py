from osprey.server.app import db
from sqlalchemy import Column, Integer, String
from osprey.server.models.source_file import SourceFile
from osprey.server.lib.error import ServiceError, MODEL_INSUFFICIENT_ATTRS, PROXYIFY_ERROR
from osprey.server.lib.proxies import proxify

class Proxy(db.Model):
    id                = Column(Integer, primary_key=True)
    representation    = Column(String)
    source_version_id = Column(Integer, db.ForeignKey('source_version.id'))
    source_version    = db.relationship("SourceVersion")

    def __init__(self, **kwargs):
        self._touch_proxy_representation(**kwargs)
        super().__init__(**kwargs)

    def __repr__(self):
        return "<Proxy(id={}, source_version_id='{}')>".format(self.id, self.source_version.id)

    def source(self):
        if self.source_version is None:
            return

        return self.source_version.source

    def toJSON(self):
        return { 
            'id': self.id,
            'serial_repr': self.representation,
            'source_version': self.source_version.toJSON() 
        }

    def _touch_proxy_representation(self, **kwargs):
        if 'source_version_id' in kwargs:
            sv_id = kwargs['source_version_id']
        elif 'source_version' in kwargs:
            sv_id = kwargs['source_version'].id
        else:
            raise ServiceError(MODEL_INSUFFICIENT_ATTRS, 'Needs source_version to create proxy')
        
        source_file = SourceFile.query.filter_by(source_version_id=sv_id).first()
        if source_file is None:
            raise ServiceError(PROXYIFY_ERROR, "Missing source file for source_version")

        self.representation = proxify(source_file.file)