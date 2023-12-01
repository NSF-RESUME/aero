from sqlalchemy import Column, Integer, String

from osprey.server.app import db


class Output(db.Model):
    id            = Column(Integer, primary_key=True)
    filename      = Column(String)
    provenance_id = db.Column(db.Integer, db.ForeignKey('provenance.id'))

    def __repr__(self):
        return f'<Output(id={self.id}, filename={self.filename}, provenance_id={self.provenance_id})>'

    def toJSON(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'provenance_id': self.provenance_id
        }