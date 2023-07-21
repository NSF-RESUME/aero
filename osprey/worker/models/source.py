import requests, datetime

from sqlalchemy.orm                import relationship
from sqlalchemy                    import Column, Integer, String
from osprey.worker.models.database import Base, Session
from osprey.worker.jobs.verifier   import verifier_microservice
from osprey.worker.lib.serializer  import encode

from osprey.worker.models.source_version import SourceVersion
from osprey.worker.models.source_file    import SourceFile

# Assume that this is sa read-only class
class Source(Base):
    __tablename__ = 'source'
    id            = Column(Integer, primary_key=True)
    name          = Column(String)
    url           = Column(String)
    description   = Column(String)
    timer         = Column(Integer) # in seconds
    verifier      = Column(String)
    versions      = relationship("SourceVersion", back_populates="source")

    def __repr__(self):
        return f"Source(id={self.id}, name={self.name}, url={self.url}, timer={self.timer_readable()})"

    def check_new_version(self):
        # NOTE : Ideally should check if its a new version, just by looking a field ig?
        # or should it do a checksum comparison?

        new_data, format = self.download()
        if not verifier_microservice(new_data, self.verifier):
            raise Exception('Need to send an email that new version failed')

        with Session() as session:
            new_version             = SourceVersion(version=self.last_verison() + 1, source_id= self.id)
            new_version.source_file = SourceFile(file=encode(new_data, format), encoding=format)
            session.add(new_version)
            session.commit()

    def download(self):
        """ 
            NOTE: Maybe in CSV or get format from user.

            But assuming that it is gonna be in JSON for now
        """
        data = requests.get(self.url)
        return data.json(), 'json'

    def last_verison(self):
        l_version = self.versions[len(self.versions) - 1]
        if not(l_version):
            return 0
        return l_version.version

    def timer_readable(self):
        if not(self.timer):
            return None

        return str(datetime.timedelta(seconds=self.timer))

"""

NOTE: This class is duplicated from the `class Source` from

    /osprey/server/models/source.py

But the usecase is, to seperates the representation for different microservices

"""