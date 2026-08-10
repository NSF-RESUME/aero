"""Removing every flow attached to a Data.

Deletes the flow that produces it and the flows that consume it, plus their
provenance. The Data, its versions, and any source type survive so flows can be
re-registered against the same UUID.
"""

from uuid import uuid4

import pytest

from sqlmodel import select

import aero.models.data
import aero.models.data_version
import aero.models.function
import aero.models.provenance

from aero.models.data import Data
from aero.models.flows import Flow
from aero.models.flows import FlowContribution
from aero.models.flows import FlowDerivation
from aero.models.flows import TriggerEnum
from aero.models.provenance import Provenance
from aero.models.provenance import ProvenanceDerivation


ROUTE = "/data"


def _fn(session):
    return aero.models.function.create_function(session=session, uuid=uuid4()).id


def _data(session, name):
    return aero.models.data.create_data(
        session=session,
        name=name,
        url=f"http://minio/{name}.csv",
        collection_url="https://globus.org/test",
        collection_uuid=uuid4(),
        description="",
    )


def _flow(session, derived_from=(), contributed_to=(), policy=TriggerEnum.NONE, **kw):
    import aero.models.flows as fm

    return fm.create_flow(
        session=session,
        derived_from=list(derived_from),
        contributed_to=list(contributed_to),
        endpoint=uuid4(),
        function_id=_fn(session),
        pull_function_id=_fn(session),
        commit_function_id=_fn(session),
        policy=policy,
        **kw,
    )


@pytest.fixture(name="no_globus", autouse=True)
def no_globus_fixture(monkeypatch):
    """Neither registration runs nor timer cancellation should reach Globus."""
    import aero.models.flows as fm
    import aero.routers.data as data_router

    monkeypatch.setattr(fm.GLOBUS_CLIENT, "run_flow", lambda **kw: None)
    cancelled = []
    monkeypatch.setattr(
        data_router.GLOBUS_CLIENT, "delete_job", lambda job_id: cancelled.append(job_id)
    )
    return cancelled


def test_deletes_the_producer_and_the_consumers(client, session):
    src = _data(session, "src")
    out = _data(session, "out")
    ingestion = _flow(session, contributed_to=[src], policy=TriggerEnum.INGESTION_EVENT)
    analysis = _flow(session, derived_from=[src], contributed_to=[out])

    resp = client.request("DELETE", f"{ROUTE}/{src.id}/flows")

    assert resp.status_code == 200, resp.text
    by_id = {e["flow_id"]: e for e in resp.json()}
    assert by_id[str(ingestion.id)]["role"] == "ingestion"
    assert by_id[str(analysis.id)]["role"] == "analysis"
    assert session.exec(select(Flow)).all() == []


def test_the_data_and_its_versions_survive(client, session):
    src = _data(session, "src")
    v = aero.models.data_version.create_dataversion(
        session=session, version=1, checksum="c1", data_id=src.id
    )
    _flow(session, contributed_to=[src])

    client.request("DELETE", f"{ROUTE}/{src.id}/flows")

    assert session.exec(select(Data).where(Data.id == src.id)).first() is not None
    assert (
        session.exec(
            select(aero.models.data_version.DataVersion).where(
                aero.models.data_version.DataVersion.id == v.id
            )
        ).first()
        is not None
    )


def test_link_and_provenance_rows_go_with_the_flow(client, session):
    """The implementation leans on SQLAlchemy clearing secondary-table rows.

    Asserted here so that behavior can't change underneath it without a failure.
    """
    src = _data(session, "src")
    out = _data(session, "out")
    v = aero.models.data_version.create_dataversion(
        session=session, version=1, checksum="c1", data_id=src.id
    )
    flow = _flow(session, derived_from=[src], contributed_to=[out])
    aero.models.provenance.create_provenance(
        session=session, flow_id=flow.id, derived_from=[v]
    )

    resp = client.request("DELETE", f"{ROUTE}/{src.id}/flows")

    assert resp.json()[0]["provenance_deleted"] == 1
    assert session.exec(select(FlowDerivation)).all() == []
    assert session.exec(select(FlowContribution)).all() == []
    assert session.exec(select(Provenance)).all() == []
    assert session.exec(select(ProvenanceDerivation)).all() == []
    # the version the provenance pointed at is not itself provenance
    assert len(src.versions) == 1


def test_unrelated_flows_are_untouched(client, session):
    src = _data(session, "src")
    other = _data(session, "other")
    _flow(session, contributed_to=[src])
    survivor = _flow(session, contributed_to=[other])

    client.request("DELETE", f"{ROUTE}/{src.id}/flows")

    remaining = session.exec(select(Flow)).all()
    assert [f.id for f in remaining] == [survivor.id]


def test_a_timer_job_is_cancelled(client, session, no_globus):
    src = _data(session, "src")
    flow = _flow(session, contributed_to=[src])
    job_id = uuid4()
    flow.timer_job_id = job_id
    session.add(flow)
    session.commit()

    resp = client.request("DELETE", f"{ROUTE}/{src.id}/flows")

    assert no_globus == [str(job_id)]
    assert resp.json()[0]["timer"] == "cancelled"


def test_a_failed_cancellation_still_deletes_and_reports(client, session, monkeypatch):
    """A Globus outage must not make flows undeletable.

    The orphaned job keeps firing, so the response has to name it -- that is the
    only way to clean it up by hand.
    """
    import aero.routers.data as data_router

    def boom(job_id):
        raise RuntimeError("timers unreachable")

    monkeypatch.setattr(data_router.GLOBUS_CLIENT, "delete_job", boom)

    src = _data(session, "src")
    flow = _flow(session, contributed_to=[src])
    job_id = uuid4()
    flow.timer_job_id = job_id
    session.add(flow)
    session.commit()

    resp = client.request("DELETE", f"{ROUTE}/{src.id}/flows")

    assert resp.status_code == 200, resp.text
    assert "NOT cancelled" in resp.json()[0]["timer"]
    assert str(job_id) == resp.json()[0]["timer_job_id"]
    assert session.exec(select(Flow)).all() == []


def test_a_data_with_no_flows_deletes_nothing(client, session):
    src = _data(session, "lonely")

    resp = client.request("DELETE", f"{ROUTE}/{src.id}/flows")

    assert resp.status_code == 200, resp.text
    assert resp.json() == []


def test_unknown_data_id_404s(client):
    assert client.request("DELETE", f"{ROUTE}/{uuid4()}/flows").status_code == 404
    assert client.get(f"{ROUTE}/{uuid4()}/flows").status_code == 404


def test_listing_tags_each_role(client, session):
    src = _data(session, "src")
    out = _data(session, "out")
    _flow(session, contributed_to=[src], policy=TriggerEnum.INGESTION_EVENT)
    _flow(session, derived_from=[src], contributed_to=[out])
    _flow(session, derived_from=[src], contributed_to=[src])  # feeds itself

    resp = client.get(f"{ROUTE}/{src.id}/flows")

    assert resp.status_code == 200, resp.text
    assert sorted(e["role"] for e in resp.json()) == ["analysis", "both", "ingestion"]


def test_listing_does_not_delete(client, session):
    src = _data(session, "src")
    _flow(session, contributed_to=[src])

    client.get(f"{ROUTE}/{src.id}/flows")

    assert len(session.exec(select(Flow)).all()) == 1
