import datetime

# from unittest import mock

# with (
#     mock.patch("osprey.server.lib.globus_search.DSaaSSearchClient") as dsc_mock,
#     mock.patch("osprey.server.jobs.timer.set_timer", return_value=1111) as st_mock,
#     mock.patch("osprey.server.jobs.user_flow.run_flow") as rf_mock,
# ):
import aero.models as models


def test_create(app):
    s: models.source.Source = models.source.Source(name="input", url="input", email="1")
    _: models.source_version.SourceVersion = models.source_version.SourceVersion(
        version=1, checksum="1", source_id=s.id
    )
    o: models.output.Output = models.output.Output(
        name="output", url="output", collection_uuid="1234"
    )
    f: models.function.Function = models.function.Function(uuid="1")
    p: models.provenance.Provenance = models.provenance.Provenance(
        function_id=f.id, derived_from=[s], contributed_to=[o]
    )

    assert (
        p.id == 1
        and p.function_id == f.id
        and p.function_args == ""
        and p.description == ""
        and p.timer is None
        and p.timer_job_id is None
        and p.policy == 3
        and p.last_executed is None
    )

    p2: models.provenance.Provenance = models.provenance.Provenance(
        function_id=f.id, derived_from=[s], contributed_to=[o], policy=0
    )
    assert p2.timer == 86400


def test_json(app):
    p: models.provenance.Provenance = models.provenance.Provenance.query.filter_by(
        id=1
    ).first()
    p_json = p.toJSON()

    assert list(p_json.keys()) == [
        "id",
        "derived_from",
        "contributed_to",
        "description",
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
    p: models.provenance.Provenance = models.provenance.Provenance.query.filter_by(
        id=1
    ).first()
    p_str = str(p)

    assert (
        p_str
        == f"<Provenance(id={p.id}, derived_from={p.derived_from}, contributed_to={p.contributed_to}, function_id={p.function_id}, function_args='{p.function_args}', timer={p.timer}, timer_job_id='{p.timer_job_id}')>"
    )


def test_start_timer_flow(app):
    p: models.provenance.Provenance = models.provenance.Provenance.query.filter_by(
        id=1
    ).first()
    assert p.timer_job_id is None

    p._start_timer_flow()
    assert p.timer_job_id == "1111"


def test_run_flow(app):
    p: models.provenance.Provenance = models.provenance.Provenance.query.filter_by(
        id=1
    ).first()
    p.policy = 0
    p.function_args = '{"endpoint": "1", "function": "1", "tasks": "1"}'

    assert p._run_flow() == 0

    before_run = datetime.datetime.now()
    p.policy = 1
    assert p._run_flow() == 1 and p.last_executed < before_run

    before_run = datetime.datetime.now()
    p.derived_from[0].add_new_version(
        new_file="nv", format="json", checksum="123", size=1
    )
    assert p._run_flow() == 1 and p.last_executed > before_run

    before_run = datetime.datetime.now()
    p.policy = 2
    assert p._run_flow() == 2 and p.last_executed < before_run

    p.derived_from[0].add_new_version(
        new_file="nv", format="json", checksum="133", size=1
    )
    assert p._run_flow() == 2 and p.last_executed > before_run
