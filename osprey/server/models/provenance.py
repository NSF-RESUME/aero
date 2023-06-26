from app import db
from sqlalchemy import Column, Integer

ProvenanceDerivation = db.Table("provenance_derivation",
                                Column('id', Integer, primary_key=True),
                                Column('provenance_id', Integer, db.ForeignKey('provenance.id')),
                                Column('previous_proxy_id',Integer, db.ForeignKey('proxy.id')))

class Provenance(db.Model):
    id             = Column(Integer, primary_key=True)
    proxy_id       = Column(Integer, db.ForeignKey('proxy.id'))
    proxy          = db.relationship("Proxy", foreign_keys=[proxy_id], back_populates='my_provenance')
    function_id    = Column(Integer, db.ForeignKey('function.id'))
    function       = db.relationship("Function")
    derived_from   = db.relationship("Proxy", secondary=ProvenanceDerivation, back_populates='provenances')

    def __repr__(self):
        return "<Provenance(id={}, proxy_id='{}', function_id='{}')>".format(self.id, self.proxy_id, self.function_id)

