import jsonschema
import requests

from datetime import datetime
from pathlib import Path
from unittest import mock
from uuid import UUID
from uuid import uuid4

import aero.models as models
from aero.app import db
from aero.worker.lib import globus_flow_helper as gfh
from aero.worker.lib.utils import schema

from aero_client.utils import load_tokens


def get_flow_inputs():
    func_id = uuid4()

    f = create_flow(func_id=func_id, inputs=True)

    derived_data = f.derived_from[0]
    derived_data.add_new_version(
        new_file="filename",
        format="json",
        checksum="1234",
        size=2,
    )

    created_data = f.contributed_to[0]

    function_params = [
        {
            "kwargs": {
                "aero": {
                    "input_data": {
                        "data1": {"id": str(derived_data.id), "version": None}
                    },
                    "output_data": {created_data.name: {"id": str(created_data.id)}},
                    "flow_id": str(f.id),
                },
                "arg1": ["apples", "pears"],
                "arg2": -100,
            },
            "endpoint": "1234",
            "function": str(func_id),
        },
        {
            "kwargs": {
                "aero": {
                    "input_data": {
                        "data1": {"id": str(derived_data.id), "version": 1000}
                    },
                    "output_data": {created_data.name: {"id": str(created_data.id)}},
                    "flow_id": str(f.id),
                },
                "arg1": ["apples", "bananas", "pears"],
                "arg2": 9999,
            },
            "endpoint": "1234",
            "function": str(func_id),
        },
    ]

    return function_params


def get_flow_outputs():
    flow_inputs = get_flow_inputs()

    for i in flow_inputs:
        i["kwargs"]["aero"]["input_data"]["data1"]["version"] = 1
        i["kwargs"]["aero"]["output_data"]["test"].update(
            {
                "filename": "1234file",
                "checksum": "checksum",
                "format": "json",
                "size": "2",
                "created_at": datetime.now().ctime(),
            }
        )

    return flow_inputs


def create_flow(func_id=UUID(int=0), inputs=False):
    f: models.function.Function = db.session.get(models.function.Function, func_id)

    if f is None:
        f: models.function.Function = models.function.Function(uuid=func_id)

    contributed_to = [create_data()]
    derived_from = []

    if inputs:
        derived_from.append(create_data())

    fl: models.flows.Flow = models.flows.Flow(
        derived_from=derived_from,
        contributed_to=contributed_to,
        endpoint=str(uuid4()),
        function_id=func_id,
        policy=models.flows.TriggerEnum.INGESTION,
        function_args={"aero": {"flow_id": "test"}},
    )
    return fl


def create_data():
    collection_uuid = "1234"
    collection_url = "https://httpbin.org/put"
    description = "test"

    d: models.data.Data = models.data.Data(
        name="test",
        url="https://httpbin.org/get",
        collection_uuid=collection_uuid,
        collection_url=collection_url,
        description=description,
    )

    return d


def test_download(app):
    f = create_flow()

    # kwargs = {"temp_dir": "/tmp", "flow_id": str(f.id)}
    kwargs = {
        "aero": {
            "output_data": {f.contributed_to[0].name: {"temp_dir": "/tmp"}},
            "flow_id": str(f.id),
        }
    }

    args, kwargs = gfh.download(**kwargs)
    test_output = kwargs["aero"]["output_data"]["test"]

    assert sorted(test_output.keys()) == [
        "checksum",
        "download",
        "file",
        "file_bn",
        "file_format",
        "id",
        "size",
        "temp_dir",
    ]

    assert Path(test_output["file"]).exists()

    data = f.contributed_to[0].id
    assert test_output["id"] == str(data)
    assert test_output["file_format"] == ".json"
    assert test_output["temp_dir"] == "/tmp"

    test_output.pop("temp_dir")
    args, kwargs = gfh.download(**kwargs)
    test_output = kwargs["aero"]["output_data"]["test"]

    assert test_output["temp_dir"] == str(Path.home() / "aero")


# def test_user_function(app):
#     f = create_flow()
#     kwargs = {"temp_dir": "/tmp", "flow_id": str(f.id)}
#     args, kwargs_download = gfh.download(**kwargs)

#     f.function_id = None

#     args, kwargs_function = gfh.user_function_wrapper(*args, **kwargs_download)

#     assert sorted(kwargs_download.items()) == sorted(kwargs_function.items())

#     f = create_flow(func_id=uuid4())
#     kwargs_download["flow_id"] = str(f.id)

#     with mock.patch(
#         "aero.globus.compute.execute_function", return_value=(args, kwargs_download)
#     ):
#         args, kwargs_function = gfh.user_function_wrapper(*args, **kwargs_download)
#         assert kwargs_function == kwargs_download

#     with mock.patch("aero.globus.compute.execute_function", return_value=None):
#         args, kwargs_function = gfh.user_function_wrapper(*args, **kwargs_download)
#         assert kwargs_function == kwargs_download

#     with mock.patch(
#         "aero.globus.compute.execute_function", side_effect=Exception("test")
#     ):
#         with pytest.raises(ServiceError):
#             args, kwargs_function = gfh.user_function_wrapper(*args, **kwargs_download)
#             print(kwargs_function)


def test_db_commit(app):
    f = create_flow(func_id=uuid4())
    kwargs = {
        "aero": {
            "output_data": {"test": {"temp_dir": "/tmp"}},
            "flow_id": str(f.id),
        }
    }
    args, kwargs_download = gfh.download(**kwargs)

    tokens = load_tokens()
    tokens["1234"] = {"autorization_token": "2345", "access_token": "2222"}

    with (
        mock.patch("aero_client.utils.load_tokens", return_value=tokens),
        mock.patch(
            "requests.put", return_value=requests.put("https://httpbin.org/put")
        ),
    ):
        response = gfh.database_commit(*args, **kwargs_download)
        assert response["success"] is True
        assert not Path(kwargs_download["aero"]["output_data"]["test"]["file"]).exists()


def test_get_version(app):
    function_params = get_flow_inputs()

    for tasks in function_params:
        jsonschema.validate(tasks["kwargs"], schema=schema)

    params = gfh.get_versions(*function_params)

    assert params[0]["kwargs"]["aero"]["input_data"]["data1"]["version"] == 1
    assert params[1]["kwargs"]["aero"]["input_data"]["data1"]["version"] == 1000


def test_commit(app):
    out_params = get_flow_outputs()

    for params in out_params:
        response = gfh.commit_analysis(**params["kwargs"])

        assert (
            params["kwargs"]["aero"]["input_data"]["data1"]["id"]
            == response["derived_from"][0]["data"]["id"]
        )
        assert (
            params["kwargs"]["aero"]["input_data"]["data1"]["version"]
            == response["derived_from"][0]["version"]
        )

        assert "test" == response["contributed_to"][0]["data"]["name"]
        assert params["kwargs"]["aero"]["flow_id"] == response["flow_id"]
