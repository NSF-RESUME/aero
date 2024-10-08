import json
from uuid import uuid4

import aero.models as models


ROUTE = "/osprey/api/v1.0/flow"

FLOW_KEYS = sorted(
    [
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
)


def analysis_flow_inputs():
    # generate input data first
    args = [{"arg1": 2, "arg2": 1}, {"arg2": 3, "arg1": 4}]
    data1 = models.data.Data(
        name="data1",
        collection_uuid=str(uuid4()),
        collection_url="https://httpbin.org/put",
        description="test data",
        url="https://httpbin.org/get",
    )

    data2 = models.data.Data(
        name="data2",
        collection_uuid=str(uuid4()),
        collection_url="https://httpbin.org/put",
        description="test dat2",
        url="https://httpbin.org/get",
    )

    data1.add_new_version(
        new_file="test1",
        format="csv",
        checksum="1234",
        size=1,
    )

    data2.add_new_version(
        new_file="test2",
        format="json",
        checksum="5555",
        size=10,
    )

    out = models.data.Data(
        name="out",
        collection_uuid=str(uuid4()),
        collection_url="https://httpbin.org/put",
        description="test dat2",
    )

    input_data = {
        "data1": {"id": str(data1.id), "version": 1},
        "data2": {"id": str(data2.id), "version": 1},
    }
    output_data = {"out": {"id": str(out.id)}}
    endpoint = str(uuid4())
    function_id = str(uuid4())
    description = "some test flow"
    function_args = args
    policy = models.flows.TriggerEnum.ANY_INPUT

    f_inputs = {
        "input_data": input_data,
        "output_data": output_data,
        "gc_endpoint": endpoint,
        "function_uuid": function_id,
        "description": description,
        "flow_kwargs": function_args,
        "collection_uuid": str(uuid4()),
        "collection_url": "https://httpbin.org/put",
        "rule": policy,
    }

    return f_inputs


def test_show_flow(client):
    response = client.get(ROUTE, follow_redirects=True)
    assert response.status_code == 200
    assert all([sorted(r.keys()) == FLOW_KEYS for r in response.json]) is True


def test_register_flow(client):
    flow_data = analysis_flow_inputs()

    headers = {"Content-Type": "application/json"}
    response = client.post(f"{ROUTE}/register", json=flow_data, headers=headers)

    assert response.status_code == 200, response.data

    assert len(json.loads(json.loads(response.data)["function_args"])) == len(
        json.loads(flow_data["flow_kwargs"])
    )


# def test_add_record(client):
#     name = "test_prov_1234"
#     function_id = uuid4()
#     filename = f"test-{uuid4()}.txt"
#     args = '{ "test": true }'

#     inputs = [i.id for i in models.data.Data.query.all()]
#     headers = {"Content-Type": "application/json"}
#     data = {
#         "data": inputs,
#         "kwargs": args,
#         "description": "A test provenance example",
#         "collection_uuid": "1234",
#         "collection_url": "https://1234",
#         "name": name,
#         "function_uuid": function_id,
#         "output_fn": filename,
#         "url": "www.test.com",
#         "checksum": "123",
#         "format": "csv",
#         "size": 2,
#         "endpoint": "1234",
#     }
#     response = client.post(f"{ROUTE}/new", json=data, headers=headers)
#     assert response.status_code == 200, response.json

#     prev_funcs = models.function.Function.query.filter(
#         models.function.Function.id == function_id
#     ).first()
#     prev_outputs = models.data.Data.query.filter(models.data.Data.name == name).first()
#     prev_num_funcs = len(
#         models.function.Function.query.filter(
#             models.function.Function.id == function_id
#         ).all()
#     )
#     prev_num_prov = len(
#         models.flows.Flow.query.filter(
#             models.flows.Flow.function_id == prev_funcs.id
#             and models.flows.Flow.function_args == args
#         ).all()
#     )
#     prev_num_outputs = len(
#         models.data.Data.query.filter(models.data.Data.name == name).all()
#     )
#     prev_num_output_versions = len(
#         models.data_version.DataVersion.query.filter(
#             models.data_version.DataVersion.data_id == prev_outputs.id
#         ).all()
#     )

#     assert (
#         prev_num_funcs == 1
#         and prev_num_outputs == 1
#         and prev_num_prov == 1
#         and prev_num_output_versions == 1
#     )

#     # rerun with missing function uuid and ensure it succeeds
#     _ = data.pop("function_uuid")
#     response = client.post(f"{ROUTE}/new", json=data, headers=headers)
#     assert response.status_code == 200, response.json

#     # rerun with existing function uuid but different args
#     _ = data["kwargs"]

#     data["kwargs"] = '{ "test": false }'
#     data["function_uuid"] = function_id
#     response = client.post(f"{ROUTE}/new", json=data, headers=headers)
#     assert response.status_code == 200, response.json

#     # test with no input sources
#     data = {
#         "kwargs": args,
#         "description": "A test provenance example",
#         "collection_uuid": "1234",
#         "name": name,
#         "function_uuid": function_id,
#         "output_fn": filename,
#         "url": "www.test.com",
#         "checksum": "123",
#         "format": "csv",
#         "size": 2,
#     }
#     response = client.post(f"{ROUTE}/new", json=data, headers=headers)
#     assert response.status_code == 200, response.json


# def test_register_flow(client):
#     name = "test_prov_1234567"
#     function_id = uuid4()
#     filename = "test.txt"
#     args = '{ "test": true }'

#     headers = {"Content-Type": "application/json"}
#     data = {
#         "data": [i.id for i in models.data.Data.query.all()],
#         "kwargs": args,
#         "collection_uuid": "1234",
#         "collection_url": "https://1234",
#         "description": "A test provenance example",
#         "name": name,
#         "function_uuid": function_id,
#         "output_fn": filename,
#         "url": "www.test.com",
#         "checksum": "123",
#         "format": "json",
#         "size": 2,
#         "endpoint": "1234",
#     }

#     # create prov record
#     response = client.post(f"{ROUTE}/new", json=data, headers=headers)

#     assert response.status_code == 200, response.text

#     response = client.post(f"{ROUTE}/timer/{function_id}", json=data, headers=headers)
#     assert response.status_code == 200, response.text

#     # with new function id
#     function_id = uuid4()
#     response = client.post(f"{ROUTE}/timer/{function_id}", json=data, headers=headers)
#     assert response.status_code == 200

#     # without outputs
#     data.pop("name")
#     data.pop("url")

#     function_id = uuid4()
#     response = client.post(f"{ROUTE}/timer/{function_id}", json=data, headers=headers)
#     assert response.status_code == 200

#     # test with policies
#     data["policy"] = 0
#     response = client.post(f"{ROUTE}/timer/{function_id}", json=data, headers=headers)
#     assert response.status_code == 200

#     data["policy"] = 1
#     response = client.post(f"{ROUTE}/timer/{function_id}", json=data, headers=headers)
#     assert response.status_code == 200

#     # without sources
#     data.pop("data")
#     response = client.post(f"{ROUTE}/timer/{function_id}", json=data, headers=headers)
#     assert response.status_code == 200
