import pytest

from unittest import mock

with (
    mock.patch("osprey.server.lib.globus_search.DSaaSSearchClient") as dsc_mock,
    mock.patch("osprey.server.jobs.timer.set_timer", return_value=1111) as st_mock,
    mock.patch("osprey.server.jobs.user_flow.run_flow") as rf_mock,
):
    from osprey.server.app import create_app, db


@pytest.fixture(scope="session")
def app():
    app = create_app()
    app.config.update({"TESTING": True})
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()
