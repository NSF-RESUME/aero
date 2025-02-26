import pytest

# import aero
# import aero.globus
# import aero.models.tag

from uuid import uuid4

import aero.models
import aero.models.data
import aero.models.data_version
import aero.models.data_file
import aero.models.function
import aero.models.flows
import aero.models.provenance


@pytest.fixture(name="data")
def data_fixture(globus_mock, session):
    name = "test"
    url = "test.com"
    collection_uuid = uuid4()
    collection_url = "https://1234"
    description = "testdescription"

    data = aero.models.data.create_data(
        session=session,
        name=name,
        url=url,
        collection_uuid=collection_uuid,
        collection_url=collection_url,
        description=description,
    )

    return data


@pytest.fixture(name="version")
def version_fixture(globus_mock, session, data):
    version = 1
    checksum = "chksm"
    v = aero.models.data_version.create_dataversion(
        session=session, version=version, checksum=checksum, data_id=data.id
    )

    return v


@pytest.fixture(name="file")
def file_fixture(globus_mock, session, version):
    file_name = "file.name"
    size = 1
    f = aero.models.data_file.create_datafile(
        session=session, file_name=file_name, size=size, version_id=version.id
    )

    return f


@pytest.fixture(name="function")
def function_fixture(globus_mock, session, flow):
    uuid = uuid4()
    func = aero.models.function.create_function(
        session=session, uuid=uuid, flows=[flow]
    )

    return func


@pytest.fixture(name="flow")
def flow_fixture(globus_mock, session, data):
    func = aero.models.function.create_function(session=session, uuid=uuid4())
    p_func = aero.models.function.create_function(session=session, uuid=uuid4())
    c_func = aero.models.function.create_function(session=session, uuid=uuid4())

    flow = aero.models.flows.create_flow(
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
def provenance_fixture(globus_mock, session, flow, version):
    prov = aero.models.provenance.create_provenance(
        session=session, flow_id=flow.id, contributed_to=[version]
    )
    return prov
