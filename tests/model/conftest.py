import pytest

from uuid import uuid4

import aero.automate.policy
import aero.automate.timer
import aero.globus.search
from aero.models.data import create_data
from aero.models.data_file import create_datafile
from aero.models.data_version import create_dataversion
from aero.models.flows import create_flow
from aero.models.function import create_function
from aero.models.provenance import create_provenance


@pytest.fixture(name="globus_mock", autouse=True)
def _mock_globus(monkeypatch):
    def mock_run_flow(*args, **kwargs):
        pass

    def mock_set_timer(*args, **kwargs):
        return uuid4()

    class MockSearchClient:
        def __init__(self, idx):
            self.index = idx

        def add_entry(self, data_version):
            return "entry has been added"

    monkeypatch.setattr("aero.models.flows.run_flow", mock_run_flow)
    monkeypatch.setattr("aero.models.flows.set_timer", mock_set_timer)
    monkeypatch.setattr(aero.globus.search, "AEROSearchClient", MockSearchClient)
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


@pytest.fixture(name="file")
def file_fixture(session, version):
    file_name = "file.name"
    size = 1
    f = create_datafile(
        session=session, file_name=file_name, size=size, version_id=version.id
    )

    return f


@pytest.fixture(name="function")
def function_fixture(session, flow):
    uuid = uuid4()
    func = create_function(session=session, uuid=uuid, flows=[flow])

    return func


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


@pytest.fixture(name="provenance")
def provenance_fixture(session, flow, version):
    prov = create_provenance(session=session, flow_id=flow.id, contributed_to=[version])
    return prov
