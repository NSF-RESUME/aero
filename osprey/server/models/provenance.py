from osprey.server.app import db
from sqlalchemy import Column, Integer

ProvenanceDerivation = db.Table("provenance_derivation",
                                Column('id', Integer, primary_key=True),
                                Column('provenance_id', Integer, db.ForeignKey('provenance.id')),
                                Column('previous_source_version_id',Integer, db.ForeignKey('source_version.id')))

class Provenance(db.Model):
    id                 = Column(Integer, primary_key=True)
    source_version_id  = Column(Integer, db.ForeignKey('source_version.id'))
    source_version     = db.relationship("SourceVersion", foreign_keys=[source_version_id], back_populates='provenance')
    function_id    = Column(Integer, db.ForeignKey('function.id'))
    function       = db.relationship("Function")
    derived_from   = db.relationship("SourceVersion", secondary=ProvenanceDerivation, back_populates='contributed_to')

    def __repr__(self):
        return "<Provenance(id={}, proxy_id='{}', function_id='{}')>".format(self.id, self.proxy_id, self.function_id)

