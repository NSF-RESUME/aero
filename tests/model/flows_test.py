import pytest

from uuid import uuid4

import aero
import aero.models


def test_create_flow(session, data):
    func = aero.models.function.create_function(session=session, uuid=uuid4())
    p_func = aero.models.function.create_function(session=session, uuid=uuid4())
    c_func = aero.models.function.create_function(session=session, uuid=uuid4())

    func_args = [{"aero": {}, "arg1": 1}, {"aero": {}, "arg2": 2}]
    flow = aero.models.flows.create_flow(
        session=session,
        derived_from=[data],
        contributed_to=[],
        endpoint=uuid4(),
        function_id=func.id,
        pull_function_id=p_func.id,
        commit_function_id=c_func.id,
        function_args=func_args,
    )

    assert "aero" in flow.function_args[0]["kwargs"]
    assert str(flow.id) in flow.function_args[0]["kwargs"]["aero"]["flow_id"]
    assert flow.policy == aero.models.flows.TriggerEnum.NONE

    func_args = {"aero": {}, "arg1": 1, "arg2": 2}
    flow = aero.models.flows.create_flow(
        session=session,
        derived_from=[data],
        contributed_to=[],
        endpoint=uuid4(),
        function_id=func.id,
        pull_function_id=p_func.id,
        commit_function_id=c_func.id,
        function_args=func_args,
        policy=aero.models.flows.TriggerEnum.INGESTION,
    )
    assert len(flow.derived_from) == 1
    assert len(flow.contributed_to) == 0


def test_start_timer(session, flow):
    flow.timer = 86400
    timer_job_id = flow._start_timer_flow(session=session)
    assert flow.timer_job_id == timer_job_id


def test_start_ingestion(session, flow):
    flow.timer = 86400
    timer_job_id = flow._start_ingestion_flow(session=session)
    assert flow.timer_job_id == timer_job_id

    with pytest.raises(aero.models.error.ServiceError):
        timer_job_id = flow._start_ingestion_flow(session=session)


def test_run_flow(session, flow, version):
    flow.timer = 86400
    flow.policy = aero.models.flows.TriggerEnum.INGESTION

    flow._run_flow(session)
    assert flow.timer_job_id is not None

    flow.timer_job_id = None
    flow.policy = aero.models.flows.TriggerEnum.TIMER
    flow._run_flow(session)
    assert flow.timer_job_id is not None

    flow.policy = aero.models.flows.TriggerEnum.ANY_INPUT
    flow.last_executed = None
    flow._run_flow(session)
    assert flow.last_executed is not None
    last_exec = flow.last_executed
    flow.derived_from[0].versions = [version]
    flow._run_flow(session)
    assert flow.last_executed == last_exec

    flow.policy = aero.models.flows.TriggerEnum.ALL_INPUT
    flow.last_executed = None
    flow._run_flow(session)
    assert flow.last_executed is not None
    last_exec = flow.last_executed
    flow._run_flow(session)
    assert flow.last_executed == last_exec

    flow.policy = aero.models.flows.TriggerEnum.NONE
    flow.last_executed = None
    flow._run_flow(session)
    assert flow.last_executed is None
