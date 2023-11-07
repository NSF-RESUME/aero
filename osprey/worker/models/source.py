import datetime
import requests
import os

from mimetypes import guess_extension
from pathlib import Path

from sqlalchemy.orm                import relationship
from sqlalchemy                    import Column, Integer, String
from osprey.worker.models.database import Base, Session
# from osprey.worker.jobs.verifier   import verifier_microservice
from osprey.worker.lib.serializer  import encode

from osprey.worker.models.source_version import SourceVersion
from osprey.worker.models.source_file    import SourceFile
from osprey.worker.models.utils import TEMP_DIR


# Assume that this is sa read-only class
class Source(Base):
    __tablename__ = 'source'
    __table_args__ = {'extend_existing': True}
    id            = Column(Integer, primary_key=True)
    name          = Column(String)
    url           = Column(String)
    description   = Column(String)
    timer         = Column(Integer) # in seconds
    verifier      = Column(String)
    modifier      = Column(String)
    email         = Column(String)
    user_endpoint = Column(String)
    timer_job_id  = Column(String)
    flow_kind     = Column(Integer)
    versions      = relationship("SourceVersion", back_populates="source", lazy=False)

    def __repr__(self):
        return f"Source(id={self.id}, name={self.name}, url={self.url}, email={self.email}, timer={self.timer_readable()})"

    def add_new_version(self, new_file, format):
        with Session() as session:
            version_number = self.last_version() + 1
            new_version             = SourceVersion(version=version_number, source_id= self.id)

            new_version.source_file = SourceFile(encoding='utf-8',
                                                 file_type=format,
                                                 file_name=new_file,
                                                 args={
                                                     'version': version_number,
                                                     'source_id': self.id
                                                     })
            session.add(new_version)
            session.commit()

    def download(self):
        """ 
            NOTE: Maybe in CSV or get format from user.

            But assuming that it is gonna be in JSON for now
        """
        response = requests.get(self.url)
        content_type = response.headers['content-type']
        ext = guess_extension(content_type.split(';')[0])
        
        bn = os.path.basename(self.url)
        fn = os.path.join(TEMP_DIR, bn)
        
        os.makedirs(TEMP_DIR, exist_ok=True)

        with open(fn, 'w+') as f:
            f.write(response.content.decode('utf-8'))
        
        return fn, ext

    def last_version(self):
        try:
            l_version = self.versions[len(self.versions) - 1]
            return l_version.version
        except IndexError:
            return 0

    def timer_readable(self):
        if not(self.timer):
            return None

        return str(datetime.timedelta(seconds=self.timer))
    
    @classmethod
    def get(cls, source_id):
        with Session() as session:
            source = session.query(Source).get(source_id)
        return source

    # @classmethod
    # def nearest_refresh(cls):       # Assume that it runs every 5 mins
    #     with Session() as s:
    #         return s.query(cls).count()

"""

NOTE: This class is duplicated from the `class Source` from

    /osprey/server/models/source.py

But the usecase is, to seperates the representation for different microservices

"""
