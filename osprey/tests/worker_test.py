import os
from pathlib import Path


from osprey.worker.models.database import Session
from osprey.worker.models.source import Source
from osprey.worker.models.utils import TEMP_DIR

from osprey.tests.utils import DUMMY_URL


def test_download():
    with Session() as _:
        s = Source(name="test", url=DUMMY_URL)
        fn, ext = s.download()
        assert os.path.join(TEMP_DIR, os.path.basename(DUMMY_URL)) == fn
        assert ext == ".json"


def test_commit(mocker):
    with Session():
        _ = mocker.patch("sqlalchemy.orm.session.Session.commit")

        s = Source(id=1, name="test", url=DUMMY_URL)
        new_path = Path(TEMP_DIR, os.path.basename(DUMMY_URL))
        s.add_new_version(new_file=new_path, format=".json")
        output_path = Path("./dsaas_storage/source/1/1/1.json")
        assert output_path.is_file()
