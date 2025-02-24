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

    response = client.post(f"{ROUTE}/register", json=flow_data, headers=headers)
    response_data = response.json()
    assert response.status_code == 501
