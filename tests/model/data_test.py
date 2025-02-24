import datetime

from uuid import uuid4

from sqlmodel import Session

from aero.models.data import create_data
from aero.models.data_version import DataVersion
from aero.models.flows import TriggerEnum


def test_create_data(session: Session):
    name = "test"
    url = "test.com"
    collection_uuid = uuid4()
    collection_url = "https://1234"
    description = "testdescription"

    s = create_data(
        session=session,
        name=name,
        url=url,
        collection_uuid=collection_uuid,
        collection_url=collection_url,
        description=description,
    )

    assert (
        s.name == name
        and s.url == url
        and s.collection_uuid == collection_uuid
        and s.collection_url == collection_url
        and s.description == description
        and s.versions == []
        and s.tags == []
    )


def test_add_new_version(session: Session, data):
    new_file = "newfile.txt"
    fmt = "txt"
    checksum = "2222"
    size = 1
    data.add_new_version(
        session=session, new_file=new_file, format=fmt, checksum=checksum, size=size
    )

    assert len(data.versions) == 1
    assert data.versions[0].version == 1
    assert isinstance(data.versions[0].created_at, datetime.datetime)

    data.add_new_version(
        session=session, new_file=new_file, format=fmt, checksum=checksum, size=size
    )

    assert len(data.versions) == 1
    assert data.versions[0].version == 1

    checksum = "3333"
    data.add_new_version(
        session=session, new_file=new_file, format=fmt, checksum=checksum, size=size
    )

    assert len(data.versions) == 2
    assert data.versions[-1].version == 2


def test_rerun_flow(session, data, flow):
    policy = data.rerun_flow(session=session)
    assert policy == [TriggerEnum.NONE]


def test_last_version(session, data):
    assert data.last_version() is None

    new_file = "newfile.txt"
    fmt = "txt"
    checksum = "2222"
    size = 1
    data.add_new_version(
        session=session, new_file=new_file, format=fmt, checksum=checksum, size=size
    )

    assert data.last_version() is not None
    assert isinstance(data.last_version(), DataVersion)
