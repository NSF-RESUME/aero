from osprey.server.app import db
from sqlalchemy import Column, Integer, String

provenance_derivation = db.Table("provenance_derivation",
                                Column('provenance_id', Integer, db.ForeignKey('provenance.id')),
                                Column('previous_source_version_id',Integer, db.ForeignKey('source_version.id')))

class Provenance(db.Model):
    id                 = Column(Integer, primary_key=True)
    function_id    = Column(Integer, db.ForeignKey('function.id'))
    function_args  = Column(String)
    description    = Column(String)
    derived_from   = db.relationship("SourceVersion", secondary=provenance_derivation, backref='source_versions', uselist=True)
    contributed_to = db.relationship("Output", backref='output', lazy=True)

    def __init__(self, function_id: str, derived_from: list, contributed_to: list):
        super().__init__(function_id=function_id, derived_from=derived_from, contributed_to=contributed_to)
        db.session.add(self)
        db.session.commit()
        

    def __repr__(self):
        return "<Provenance(id={}, derived_from={}, contributed_to={}, function_id='{}')>".format(
            self.id,
            self.derived_from,
            self.contributed_to,
            self.function_id)


    def toJSON(self):
        return { 
            'id': self.id, 
            'derived_from': [v.toJSON() for v in self.derived_from], 
            'contributed_to': self.contributed_to[0].toJSON(),
            'function_id': self.function_id
        }

