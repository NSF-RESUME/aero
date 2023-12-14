import pytest

from osprey.server.app import create_app
from osprey.server.app import db


class Config(object):
    DATABASE_HOST = "dsaas-postgres-database-1"
    DATABASE_USER = "postgres"
    DATABASE_PASSWORD = "postgres"
    DATABASE_PORT = "5432"
    DATABASE_NAME = "osprey_development"
    SQLALCHEMY_DATABASE_URI = f"postgresql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"


@pytest.fixture()
def app():
    app = create_app(Config)
    app.config.update(
        {
            "TESTING": True,
        }
    )
    yield app


@pytest.fixture()
def client(app):
    with app.test_client() as testclient:
        with app.app_context():
            db.create_all()
            yield testclient


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()
