import datetime

from uuid import uuid4

from sqlmodel import Session

import aero.models
import aero.models.data_version


def test_create_data(session: Session):
    import aero.models.data

    name = "test"
    url = "test.com"
    collection_uuid = uuid4()
    collection_url = "https://1234"
    description = "testdescription"

    s = aero.models.data.create_data(
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


def test_add_new_version_dedups_per_source_key(session: Session, data):
    """One Data fed by two objects dedups per object, not against the tail.

    A, B, then A-unchanged: comparing against the last version would see B's
    checksum and record a spurious third version.
    """
    common = {"session": session, "format": "gz", "size": 1}

    data.add_new_version(
        new_file="traffic/a.gz", checksum="aaa", source_key="traffic/a.gz", **common
    )
    data.add_new_version(
        new_file="traffic/b.gz", checksum="bbb", source_key="traffic/b.gz", **common
    )
    result = data.add_new_version(
        new_file="traffic/a.gz", checksum="aaa", source_key="traffic/a.gz", **common
    )

    assert isinstance(result, dict)  # "Version already exists"
    assert len(data.versions) == 2

    # a genuine change to A does version, and numbering stays global per Data
    data.add_new_version(
        new_file="traffic/a.gz", checksum="ccc", source_key="traffic/a.gz", **common
    )
    assert len(data.versions) == 3
    assert data.last_version().version == 3


def test_add_new_version_dedup_false_always_versions(session: Session, data):
    common = {
        "session": session,
        "format": "gz",
        "size": 1,
        "source_key": "traffic/a.gz",
    }

    data.add_new_version(new_file="traffic/a.gz", checksum="aaa", **common)
    data.add_new_version(new_file="traffic/a.gz", checksum="aaa", dedup=False, **common)

    assert len(data.versions) == 2


def test_rerun_flow(session, data, flow):
    policy = data.rerun_flow(session=session)
    assert policy == [aero.models.flows.TriggerEnum.NONE]


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
    assert isinstance(data.last_version(), aero.models.data_version.DataVersion)


def test_last_version_picks_highest_version_not_last_loaded(session, data):
    """Ordering must come from `version`, not from the relationship's load order.

    The old implementation returned ``versions[len(versions) - 1]``, so appending
    an out-of-order version made it report the wrong one — and `/data/{id}/latest`
    plus the ANY/ALL rerun gate both read this.
    """
    for number, checksum in ((1, "aaa"), (3, "ccc"), (2, "bbb")):
        session.add(
            aero.models.data_version.DataVersion(
                version=number, data_id=data.id, checksum=checksum
            )
        )
    session.commit()
    session.refresh(data)

    assert [v.version for v in data.versions] == [1, 3, 2]
    assert data.last_version().version == 3
