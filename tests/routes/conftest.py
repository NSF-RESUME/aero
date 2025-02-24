import pytest

from unittest import mock
from uuid import uuid4

from pydantic import BaseModel

from fastapi.testclient import TestClient

from typing import Any

from sqlmodel import Session
from sqlmodel import SQLModel
from sqlmodel import create_engine
from sqlmodel.pool import StaticPool

from aero.automate.policy import run_flow
from aero.database import get_session
from aero.main import app
from aero.models.data import create_data
from aero.models.data_version import create_dataversion
from aero.models.data_file import create_datafile
from aero.models.flows import create_flow
from aero.models.function import create_function


class MockedAuthClient(BaseModel):
    authorizer: Any

    def get_identities(self, usernames: str):
        return {"identities": [{"id": 1}]}


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    def run_flow_override(*args, **kwargs):
        pass

    app.dependency_overrides[get_session] = get_session_override
    app.dependency_overrides[run_flow] = run_flow

    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(name="data")
def data_fixture(session: Session):
    data = create_data(
        session=session,
        name="Test data",
        url="https://test.com",
        collection_url="https://globus.org/test",
        collection_uuid=uuid4(),
        description="",
    )

    version = create_dataversion(
        session=session, version=1, checksum="123", data_id=data.id
    )

    _ = create_datafile(
        session=session, file_name="testfile", size=2, version_id=version.id
    )
    return data


@pytest.fixture(name="noversion_data")
def noversion_data_fixture(session: Session):
    data = create_data(
        session=session,
        name="Test data",
        url="https://test.com",
        collection_url="https://globus.org/test",
        collection_uuid=uuid4(),
        description="",
    )

    return data


@pytest.fixture(name="flow")
def flow_fixture(session: Session, data, noversion_data):
    func = create_function(session=session, uuid=uuid4())
    p_func = create_function(session=session, uuid=uuid4())
    c_func = create_function(session=session, uuid=uuid4())
    flow = create_flow(
        session=session,
        derived_from=[data],
        contributed_to=[noversion_data],
        endpoint=uuid4(),
        function_id=func.id,
        pull_function_id=p_func.id,
        commit_function_id=c_func.id,
    )

    return flow


@pytest.fixture(scope="session", autouse=True)
def _mock_auth():
    with mock.patch("aero.decorators.is_token_valid", return_value=True) as _:
        yield


@pytest.fixture(scope="session", autouse=True)
def _mock_globus():
    with (
        mock.patch("aero.automate.timer.set_timer", return_value=1111) as _,
        mock.patch("aero.automate.policy.run_flow") as _,
        mock.patch("globus_sdk.AuthClient") as _,
        mock.patch("aero.globus.search.DSaaSSearchClient", autospec=True) as _,
    ):
        yield
