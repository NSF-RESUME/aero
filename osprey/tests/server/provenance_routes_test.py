import json

from pathlib import Path
from random import randint
from uuid import uuid4

from osprey.server.models.function import Function
from osprey.server.models.output import Output
from osprey.server.models.output_version import OutputVersion
from osprey.server.models.provenance import Provenance

from osprey.tests.server.conftest import db

ROUTE = "/osprey/api/v1.0/prov"
GCS_OUTPUT_DIR = Path("/dsaas_storage/output")
GCS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

PROVENANCE_KEYS = sorted(
    [
        "id",
        "derived_from",
        "contributed_to",
        "description",
        "function_id",
        "function_args",
        "timer",
        "timer_job_id",
    ]
)


def test_show_prov(client):
    response = client.get(ROUTE, follow_redirects=True)
    assert all([sorted(r.keys()) == PROVENANCE_KEYS for r in response.json]) is True


def test_add_record(client, mocker):
    mocker.patch("osprey.server.jobs.timer.set_timer")

    name = "test_prov_1234"
    function_id = "12345"
    filename = f"test-{uuid4()}.txt"
    args = '{ "test": true }'

    # Create the file
    with open(Path(GCS_OUTPUT_DIR, filename), "w+") as f:
        data = {"test": f"world{randint(0, 100)}{randint(0, 100)}{randint(0, 100)}"}
        json.dump(data, f)

    headers = {"Content-Type": "application/json"}
    data = {
        "sources": {1: 1},
        "args": args,
        "description": "A test provenance example",
        "name": name,
        "function_uuid": function_id,
        "output_fn": filename,
    }
    response = client.post(f"{ROUTE}/new/{function_id}", json=data, headers=headers)

    prev_funcs = db.session.query(Function).filter(Function.uuid == function_id).first()
    prev_outputs = db.session.query(Output).filter(Output.name == name).first()
    prev_num_funcs = len(
        db.session.query(Function).filter(Function.uuid == function_id).all()
    )
    prev_num_prov = len(
        db.session.query(Provenance)
        .filter(
            Provenance.function_id == prev_funcs.id and Provenance.function_args == args
        )
        .all()
    )
    prev_num_outputs = len(db.session.query(Output).filter(Output.name == name).all())
    prev_num_output_versions = len(
        db.session.query(OutputVersion)
        .filter(OutputVersion.source_id == prev_outputs.id)
        .all()
    )

    print(
        prev_funcs,
        prev_num_funcs,
        prev_num_outputs,
        prev_num_prov,
        prev_num_output_versions,
        response,
    )
    print(
        db.session.query(Provenance)
        .filter(
            Provenance.function_id == prev_funcs.id and Provenance.function_args == args
        )
        .order_by(Provenance.id.desc())
        .first()
    )

    # attempt to re-add the same output
    # Add different output
    # add function with different args


def test_register_flow(client, mocker):
    mocker.patch("osprey.server.jobs.timer.set_timer")

    name = "test_prov_1234567"
    function_id = "12345678"
    filename = "test.txt"
    args = '{ "test": true }'

    # Create the file
    with open(Path(GCS_OUTPUT_DIR, filename), "w+") as f:
        data = {"test": "world"}
        json.dump(data, f)

    headers = {"Content-Type": "application/json"}
    data = {
        "sources": {1: 1},
        "args": args,
        "description": "A test provenance example",
        "name": name,
        "function_uuid": function_id,
        "output_fn": filename,
    }

    # create prov record
    response = client.post(f"{ROUTE}/new/{function_id}", json=data, headers=headers)

    assert response.status_code == 200, response.text

    response = client.post(
        f"{ROUTE}/timer/{function_id}", json={"kwargs": data}, headers=headers
    )
    assert response.status_code == 200, response.text
