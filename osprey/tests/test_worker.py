import os

os.environ['DATABASE_HOST'] = '127.0.0.1'
os.environ['DATABASE_USER'] = 'postgres'
os.environ['DATABASE_PASSWORD'] = 'postgres'
os.environ['DATABASE_PORT'] = '5001'
os.environ['DATABASE_NAME'] = 'osprey_development'

from pathlib import Path

from osprey.worker.lib.globus_flow_helper import download
from osprey.worker.models.database import Session
from osprey.worker.models.source import Source
from osprey.worker.models.utils import TEMP_DIR

from osprey.tests.utils import DUMMY_URL

def test_download():
    with Session() as session:
        s = Source(name='test', url=DUMMY_URL)
        s.download()
        assert Path(TEMP_DIR, os.path.basename(DUMMY_URL)) 

def test_commit(mocker):
    with Session() as session:
        _ = mocker.patch('sqlalchemy.orm.session.Session.commit')

        s = Source(id=1, name='test', url=DUMMY_URL)
        new_path = Path(TEMP_DIR, os.path.basename(DUMMY_URL))
        s.add_new_version(new_file=new_path, format='.json')
        output_path = Path("./dsaas_storage/source/1/1/1.json")
        assert output_path.is_file()