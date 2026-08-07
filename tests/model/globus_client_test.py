"""Per-run url injection into an analysis flow's input_data.

The transient signed url must reach the run without ever being written back to
the stored ``Flow.function_args`` — that is what the deep copy is for.
"""

import json

import pytest

from aero import GLOBUS_CLIENT
from aero.globus.utils import FlowEnum
from aero.globus.utils import FLOW_IDS


SRC = "8908fc25-4f6d-46ea-814e-af4d2efcfbb5"
OTHER = "11111111-1111-1111-1111-111111111111"
TRIGGER = "http://minio:9000/traffic/a.xml.gz"
SIGNED = f"{TRIGGER}?X-Amz-Signature=abc"


@pytest.fixture(name="sent")
def sent_fixture(monkeypatch):
    """Capture the run_input that would go to the Globus flow service."""
    captured = {}

    class _Resp:
        http_status = 201

    class _FlowClient:
        def run_flow(self, body, label, run_managers):
            captured.update(body)
            return _Resp()

    monkeypatch.setitem(
        GLOBUS_CLIENT.specific_flow_clients, FLOW_IDS[FlowEnum.USER_FLOW], _FlowClient()
    )
    return captured


@pytest.fixture(name="tasks")
def tasks_fixture():
    """A two-input analysis flow's persisted function_args."""
    return {
        "kwargs": {
            "aero": {
                "input_data": {
                    "report": {"id": SRC, "version": None, "collection_url": "https://c/"},
                    "other": {"id": OTHER, "version": None, "collection_url": "https://c/"},
                }
            }
        },
        "function": "f",
        "endpoint": "e",
    }


def _run(tasks, **extra):
    GLOBUS_CLIENT.run_flow(
        endpoint_uuid="e",
        function_uuid="f",
        pull_function_uuid="p",
        commit_function_uuid="c",
        tasks=tasks,
        email=None,
        **extra,
    )


def test_urls_land_only_on_the_input_that_changed(sent, tasks):
    _run(tasks, trigger_url=TRIGGER, signed_url=SIGNED, source_data_id=SRC)

    input_data = sent["tasks"][0]["kwargs"]["aero"]["input_data"]
    assert input_data["report"]["trigger_url"] == TRIGGER
    assert input_data["report"]["signed_url"] == SIGNED
    # a sibling input resolves however it normally would
    assert "trigger_url" not in input_data["other"]


def test_stored_function_args_are_not_mutated(sent, tasks):
    before = json.dumps(tasks, sort_keys=True)

    _run(tasks, trigger_url=TRIGGER, signed_url=SIGNED, source_data_id=SRC)

    # the signed url expires; persisting it would poison every later run
    assert json.dumps(tasks, sort_keys=True) == before


def test_no_injection_without_a_trigger(sent, tasks):
    """The copy path and /prov/new-driven reruns pass no urls at all."""
    _run(tasks)

    input_data = sent["tasks"][0]["kwargs"]["aero"]["input_data"]
    assert not any("trigger_url" in entry for entry in input_data.values())


def test_trigger_without_a_signature_still_injects(sent, tasks):
    """Unsigned is a valid state: public bucket, or presigning turned off."""
    _run(tasks, trigger_url=TRIGGER, source_data_id=SRC)

    report = sent["tasks"][0]["kwargs"]["aero"]["input_data"]["report"]
    assert report["trigger_url"] == TRIGGER
    assert "signed_url" not in report
