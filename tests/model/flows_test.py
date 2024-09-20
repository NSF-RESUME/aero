import datetime
import json
import pytest

from uuid import uuid4

from aero.globus.error import ServiceError
import aero.models as models


def test_create(app):
    s: models.data.Data = models.data.Data(
        name="input",
        url="input",
        collection_uuid="1234",
        collection_url="https://1234",
        description="test",
    )
    _: models.data_version.DataVersion = models.data_version.DataVersion(
        version=1, checksum="1", data_id=s.id
    )
    o: models.data.Data = models.data.Data(
        name="output",
        url="output",
        collection_uuid="1234",
        collection_url="https://1234",
        description="test",
    )
    f: models.function.Function = models.function.Function(uuid=uuid4())
    p: models.flows.Flow = models.flows.Flow(
        function_id=f.id,
        derived_from=[s],
        contributed_to=[o],
        endpoint="1222",
        function_args=json.dumps({}),
    )

    assert (
        p.function_id == f.id
        and p.function_args == "{}"
        and p.description == ""
        and p.timer is None
        and p.timer_job_id is None
        and p.policy == -1
        and p.last_executed is None
    )

    p2: models.flows.Flow = models.flows.Flow(
        function_id=f.id,
        derived_from=[s],
        contributed_to=[o],
        policy=0,
        endpoint="1234",
        function_args=json.dumps("{}"),
    )
    assert p2.timer == 86400


def test_json(app):
    p: models.flows.Flow = models.flows.Flow.query.first()
    p_json = p.toJSON()

    assert list(p_json.keys()) == [
        "id",
        "derived_from",
        "contributed_to",
        "description",
        "endpoint",
        "function_id",
        "function_args",
        "timer",
        "policy",
        "timer_job_id",
        "last_executed",
    ]

    assert (
        p_json["id"] == p.id
        and p_json["derived_from"] == [s.toJSON() for s in p.derived_from]
        and p_json["contributed_to"] == [o.toJSON() for o in p.contributed_to]
        and p_json["description"] == p.description
        and p_json["function_id"] == p.function_id
        and p_json["function_args"] == p.function_args
        and p_json["timer"] == p.timer
        and p_json["policy"] == p.policy
        and p_json["timer_job_id"] == p.timer_job_id
        and p_json["last_executed"] == p.last_executed
    )


def test_str_repr(app):
    p: models.flows.Flow = models.flows.Flow.query.first()
    p_str = str(p)

    assert (
        p_str
        == f"<Flow(id={p.id}, derived_from={p.derived_from}, contributed_to={p.contributed_to}, function_id={p.function_id}, function_args='{p.function_args}', timer={p.timer}, timer_job_id='{p.timer_job_id}')>"
    )


def test_start_timer_flow(app):
    p: models.flows.Flow = models.flows.Flow.query.all()[-1]
    assert p.timer_job_id == "1111"

    p.timer_job_id = "1234"

    p._start_timer_flow()
    assert p.timer_job_id == "1111"


def test_run_analysis_flow(app):
    p: models.flows.Flow = models.flows.Flow.query.all()[-1]

    p.policy = models.flows.TriggerEnum.NONE
    p.function_args = '{"endpoint": "1", "function": "1", "tasks": "1"}'

    assert p._run_flow() == models.flows.TriggerEnum.NONE

    before_run = datetime.datetime.now()
    p.policy = models.flows.TriggerEnum.ANY_INPUT
    assert p.last_executed is None
    assert (
        p._run_flow() == models.flows.TriggerEnum.ANY_INPUT
        and p.last_executed > before_run
    )
    before_run = datetime.datetime.now()
    assert (
        p._run_flow() == models.flows.TriggerEnum.ANY_INPUT
        and p.last_executed < before_run
    )

    before_run = datetime.datetime.now()
    p.derived_from[0].add_new_version(
        new_file="nv", format="json", checksum="123", size=1
    )
    assert (
        p._run_flow() == models.flows.TriggerEnum.ANY_INPUT
        and p.last_executed > before_run
    )

    before_run = datetime.datetime.now()
    p.policy = models.flows.TriggerEnum.ALL_INPUT
    assert (
        p._run_flow() == models.flows.TriggerEnum.ALL_INPUT
        and p.last_executed < before_run
    )

    p.derived_from[0].add_new_version(
        new_file="nv", format="json", checksum="133", size=1
    )
    assert (
        p._run_flow() == models.flows.TriggerEnum.ALL_INPUT
        and p.last_executed > before_run
    )


def test_ingestion_flow(app):
    s: models.data.Data = models.data.Data(
        name="input",
        url="input",
        collection_uuid="1234",
        collection_url="https://1234",
        description="test",
    )

    f: models.function.Function = models.function.Function(uuid=uuid4())
    p: models.flows.Flow = models.flows.Flow(
        function_id=f.id,
        derived_from=[],
        contributed_to=[s],
        policy=models.flows.TriggerEnum.INGESTION,
        endpoint="1234",
        function_args=json.dumps({}),
    )

    with pytest.raises(ServiceError):
        _ = p._run_flow()
