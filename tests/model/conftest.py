import pytest

from uuid import uuid4
from unittest import mock

from aero.models.data import create_data
from aero.models.flows import create_flow
from aero.models.function import create_function
from aero.models.data_version import create_dataversion


@pytest.fixture(scope="session", autouse=True)
def _mock_globus():
    with (
        mock.patch("aero.automate.timer.set_timer", return_value=1111) as _,
        mock.patch("aero.automate.policy.run_flow") as _,
        mock.patch("aero.globus.search.DSaaSSearchClient", autospec=True) as _,
    ):
        yield


@pytest.fixture(name="data")
def data_fixture(session):
    name = "test"
    url = "test.com"
    collection_uuid = uuid4()
    collection_url = "https://1234"
    description = "testdescription"

    data = create_data(
        session=session,
        name=name,
        url=url,
        collection_uuid=collection_uuid,
        collection_url=collection_url,
        description=description,
    )

    return data


@pytest.fixture(name="version")
def version_fixture(session, data):
    version = 1
    checksum = "chksm"
    v = create_dataversion(
        session=session, version=version, checksum=checksum, data_id=data.id
    )

    return v


@pytest.fixture(name="flow")
def flow_fixture(session, data):
    func = create_function(session=session, uuid=uuid4())
    p_func = create_function(session=session, uuid=uuid4())
    c_func = create_function(session=session, uuid=uuid4())

    flow = create_flow(
        session=session,
        derived_from=[data],
        contributed_to=[],
        endpoint=uuid4(),
        function_id=func.id,
        pull_function_id=p_func.id,
        commit_function_id=c_func.id,
    )

    return flow
