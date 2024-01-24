import pytest

from osprey.server.app import create_app
from osprey.server.models.source import Source


@pytest.fixture
def app():
    return create_app()


def test_create_source(app):
    with app.app_context():
        _ = Source(name="test", url="test", email="test")


def test_source_populate():
    # with app.app_context():
    #    Source(name='test_populate', url=DUMMY_URL, verifier='dcf0c1d4-9ef8-41eb-b13b-8f0156b206bd')
    pass
