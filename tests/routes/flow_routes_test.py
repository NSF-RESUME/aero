from uuid import uuid4

import aero.models as models


ROUTE = "/flow"

FLOW_KEYS = sorted(
    [
        "id",
        "description",
        "user_endpoint",
        "pull_function_id",
        "commit_function_id",
        "arg_hash",
        "function_id",
        "function_args",
        "timer",
        "policy",
        "timer_job_id",
        "last_executed",
        "email",
        "contributed_to",
        "derived_from",
    ]
)


def test_show_flows(client, flow):
    response = client.get(ROUTE, follow_redirects=True)
    resp_data = response.json()
    assert response.status_code == 200
    assert len(resp_data) == 1
    assert all([sorted(r.keys()) == FLOW_KEYS for r in resp_data]) is True


def test_get_flows(client, flow):
    response = client.get(f"{ROUTE}/{flow.id}", follow_redirects=True)
    resp_data = response.json()
    assert response.status_code == 200
    assert resp_data["id"] == str(flow.id)
    assert sorted(resp_data.keys()) == FLOW_KEYS

    flow_id = uuid4()
    response = client.get(f"{ROUTE}/{flow_id}", follow_redirects=True)
    assert response.status_code == 404


def test_register_flow(client, data, noversion_data, flow):
    args = [{"arg1": 2, "arg2": 1}, {"arg2": 3, "arg1": 4}]
    input_data = {
        "data1": {"id": str(data.id), "version": 1},
    }
    output_data = {
        "out": {
            "id": str(noversion_data.id),
            "collection_uuid": str(noversion_data.collection_uuid),
            "collection_url": noversion_data.collection_url,
        }
    }
    endpoint = str(uuid4())
    function_id = str(uuid4())
    description = "some test flow"
    function_args = args
    policy = models.flows.TriggerEnum.ANY_INPUT

    flow_data = {
        "input_data": input_data,
        "output_data": output_data,
        "gc_endpoint": endpoint,
        "function_uuid": function_id,
        "description": description,
        "flow_kwargs": function_args,
        "commit_function_uuid": str(uuid4()),
        "pull_function_uuid": str(uuid4()),
        "rule": policy,
    }

    headers = {"Content-Type": "application/json"}
    response = client.post(f"{ROUTE}/register", json=flow_data, headers=headers)
    response_data = response.json()

    assert response.status_code == 200, response.json()
    assert len(response_data["function_args"]) == len(flow_data["flow_kwargs"])

    flow_data["flow_kwargs"] = {"arg1": 1}
    flow_data["function_uuid"] = str(flow.function.id)
    flow_data["pull_function_uuid"] = str(flow.pull_function_id)
    flow_data["commit_function_uuid"] = str(flow.commit_function_id)
    flow_data["output_data"]["out"]["url"] = "123test"
    response = client.post(f"{ROUTE}/register", json=flow_data, headers=headers)
    response_data = response.json()
    assert response.status_code == 200
    assert "contributed_to" in response_data

    response = client.post(f"{ROUTE}/register", json=flow_data, headers=headers)
    response_data = response.json()
    assert response.status_code == 501


def test_register_sources_share_function_distinct_outputs(client):
    """Different sources sharing one staging function must both register.

    Regression: two INGESTION_EVENT sources have the same function and empty
    input_data/flow_kwargs, differing only in output_data (url/name). The
    arg_hash used to exclude output_data, so the second registration falsely
    returned 501 "Flow already exists".
    """
    stage_fn = str(uuid4())
    pull_fn = str(uuid4())
    commit_fn = str(uuid4())
    headers = {"Content-Type": "application/json"}

    def source_payload(name, url, collection_uuid):
        return {
            "input_data": {},
            "output_data": {
                name: {
                    "url": url,
                    "collection_uuid": collection_uuid,
                    "collection_url": "https://g.data.globus.org/",
                }
            },
            "gc_endpoint": str(uuid4()),
            "function_uuid": stage_fn,
            "commit_function_uuid": commit_fn,
            "pull_function_uuid": pull_fn,
            "description": "",
            "flow_kwargs": {},
            "rule": models.flows.TriggerEnum.INGESTION_EVENT,
        }

    coll = str(uuid4())
    payload_a = source_payload("src-a", "http://minio:9000/bucket/a.csv", coll)

    r1 = client.post(f"{ROUTE}/register", json=payload_a, headers=headers)
    assert r1.status_code == 200, r1.json()

    # different source (name + url), SAME staging function -> must succeed
    payload_b = source_payload("src-b", "http://minio:9000/bucket/b.csv", str(uuid4()))
    r2 = client.post(f"{ROUTE}/register", json=payload_b, headers=headers)
    assert r2.status_code == 200, r2.json()

    # an identical source is still deduped
    r_dup = client.post(f"{ROUTE}/register", json=payload_a, headers=headers)
    assert r_dup.status_code == 501, r_dup.json()
