import pytest

from unittest import mock

# dsc_mock = mock.patch("osprey.server.lib.globus_search.DSaaSSearchClient")
# st_mock = mock.patch("osprey.server.jobs.timer.set_timer", return_value=1111)
# rf_mock = mock.patch("osprey.server.jobs.user_flow.run_flow")

from aero.app import create_app, db


@pytest.fixture(scope="session")
def app():
    app = create_app()
    app.config.update({"TESTING": True})
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope="session", autouse=True)
def _mock_globus():
    with (
        mock.patch("aero.automate.timer.set_timer", return_value=1111) as _,
        mock.patch("aero.automate.policy.run_flow") as _,
        mock.patch("aero.globus.search.DSaaSSearchClient", autospec=True) as _,
    ):
        yield


@pytest.fixture()
def client(app):
    return app.test_client()
