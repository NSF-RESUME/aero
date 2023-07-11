from osprey.server.app import db
from sqlalchemy import Column, Integer, String
from osprey.server.models.provenance import ProvenanceDerivation

class Proxy(db.Model):
    id                = Column(Integer, primary_key=True)
    representation    = Column(String)
    source_version_id = Column(Integer, db.ForeignKey('source_version.id'))
    source_version    = db.relationship("SourceVersion")
    my_provenance     = db.relationship("Provenance", back_populates='proxy')
    provenances       = db.relationship("Provenance", secondary=ProvenanceDerivation, back_populates='derived_from')

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