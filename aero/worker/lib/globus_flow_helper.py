"""

NOTE:

1. Stop download if its the same file
2. Direct download using HTTPS using gcs
3. Work on authentication
    i) Use Funcx credentials to register all functions
    ii) Avoid using sudershan@uchicago.edu identity for all globus services

"""

from aero.globus.compute import register_function


def download(*args, **kwargs):
    """Download data from user-specified repository.

    Returns:
        tuple[str, str]: Path to the data and its
            associated extension.
    """
    import hashlib
    import pathlib
    import requests
    import uuid
    from mimetypes import guess_extension
    from pathlib import Path

    from aero_client.config import CONF
    from aero_client.utils import load_tokens

    outputs = list(kwargs["aero"]["output_data"].items())

    if "temp_dir" in outputs[0][1]:
        TEMP_DIR = Path(outputs[0][1]["temp_dir"])
    else:
        TEMP_DIR = pathlib.Path.home() / "aero"
        outputs[0][1]["temp_dir"] = str(TEMP_DIR)

    tokens = load_tokens()
    auth_token = tokens[CONF.portal_client_id]["refresh_token"]

    headers = {"Authorization": f"Bearer {auth_token}"}

    # assert False, CONF.server_url
    response = requests.get(
        f'{CONF.server_url}/flow/{kwargs["aero"]["flow_id"]}',
        headers=headers,
        verify=False,
    )
    flow = response.json()

    data = flow["contributed_to"][
        0
    ]  # assuming only one contribution / ingesting flow for now

    response = requests.get(data["url"])
    content_type = response.headers["content-type"]
    ext = guess_extension(content_type.split(";")[0])

    bn = str(uuid.uuid4())
    fn = Path(TEMP_DIR, bn)

    TEMP_DIR.mkdir(exist_ok=True, parents=True)

    with open(fn, "w+") as f:
        f.write(response.content.decode("utf-8"))

    kwargs["aero"]["output_data"][data["name"]]["id"] = data["id"]
    kwargs["aero"]["output_data"][data["name"]]["file"] = str(fn)
    kwargs["aero"]["output_data"][data["name"]]["file_bn"] = bn
    kwargs["aero"]["output_data"][data["name"]]["file_format"] = ext
    kwargs["aero"]["output_data"][data["name"]]["checksum"] = hashlib.md5(
        response.content
    ).hexdigest()
    kwargs["aero"]["output_data"][data["name"]]["size"] = fn.stat().st_size
    kwargs["aero"]["output_data"][data["name"]]["download"] = True

    return args, kwargs


# def user_function_wrapper(*args, **kwargs):
#     import requests

#     from uuid import UUID

#     from aero_client.config import CONF
#     from aero_client.utils import load_tokens

#     from aero.globus.error import ServiceError, CUSTOM_FUNCTION_ERROR
#     from aero.globus.compute import execute_function

#     tokens = load_tokens()
#     auth_token = tokens[CONF.portal_client_id]["refresh_token"]
#     headers = {"Authorization": f"Bearer {auth_token}"}

#     flow_id = kwargs["flow_id"]

#     response = requests.get(
#         f"{CONF.server_url}/flow/{flow_id}", headers=headers, verify=False
#     )

#     assert response.status_code == 200, response.content
#     flow = response.json()

#     # Verifier
#     null_uuid = str(UUID(int=0))
#     if flow["function_id"] != null_uuid:
#         try:
#             result = execute_function(
#                 flow["function_id"], flow["endpoint"], *args, **kwargs
#             )
#             if result is not None:
#                 args, kwargs = result
#         except Exception:
#             raise ServiceError(
#                 CUSTOM_FUNCTION_ERROR, "Verifier/Transformation function failed"
#             )

#     # TODO: check if data has changed

#     return args, kwargs


def database_commit(*args, **kwargs):
    import json
    import pathlib
    import requests
    from aero_client.config import CONF
    from aero_client.utils import load_tokens

    tokens = load_tokens()

    auth_token = tokens[CONF.portal_client_id]["refresh_token"]
    aero_headers = {"Authorization": f"Bearer {auth_token}"}

    output_items = list(kwargs["aero"]["output_data"].items())

    data_id = output_items[0][1]["id"]
    file_bn = output_items[0][1]["file_bn"]

    # get source
    response = requests.get(
        f"{CONF.server_url}/data/{data_id}", headers=aero_headers, verify=False
    )
    data = response.json()

    gcs_url = data["collection_url"]
    gcs_id = data["collection_uuid"]

    transfer_token = tokens[gcs_id]["access_token"]

    headers = {"Authorization": f"Bearer {transfer_token}"}

    with open(output_items[0][1]["file"], "r") as f:
        data = f.read()

    # save data to GCS
    response = requests.put(f"{gcs_url}/{file_bn}", headers=headers, data=data)

    assert response.status_code == 200, response.json()

    aero_headers["Content-type"] = "application/json"

    # add new version
    response = requests.post(
        f"{CONF.server_url}/data/{data_id}/new-version",
        headers=aero_headers,
        verify=False,
        data=json.dumps(
            {
                "file": output_items[0][1]["file_bn"],
                "file_format": output_items[0][1]["file_format"],
                "checksum": output_items[0][1]["checksum"],
                "size": output_items[0][1]["size"],
            }
        ),
    )

    # add provenance
    response = requests.post(
        f"{CONF.server_url}/prov/new",
        headers=aero_headers,
        verify=False,
        data=json.dumps(kwargs),
    )

    pathlib.Path(output_items[0][1]["file"]).unlink()
    assert response.status_code == 200, response.json()
    return response.json()


def get_versions(*function_params):
    import requests
    from aero_client.config import CONF
    from aero_client.utils import load_tokens

    tokens = load_tokens()

    auth_token = tokens[CONF.portal_client_id]["refresh_token"]
    aero_headers = {"Authorization": f"Bearer {auth_token}"}

    for params in function_params:
        kw = params["kwargs"]

        assert "aero" in kw.keys()

        for name, md in kw["aero"]["input_data"].items():
            if md["version"] is None:
                response = requests.get(
                    f"{CONF.server_url}/data/{md['id']}/latest",
                    headers=aero_headers,
                    verify=False,
                )

                assert response.status_code == 200, response.content
                md["version"] = response.json()["data_version"]["version"]

    return function_params


def commit_analysis(*arglist):
    import json
    import requests
    from aero_client.config import CONF
    from aero_client.utils import load_tokens

    tokens = load_tokens()

    auth_token = tokens[CONF.portal_client_id]["refresh_token"]
    aero_headers = {"Authorization": f"Bearer {auth_token}"}
    aero_headers["Content-type"] = "application/json"

    responses = []
    for task_kwargs in arglist:
        assert "input_data" in task_kwargs["aero"]
        assert "output_data" in task_kwargs["aero"]
        assert "flow_id" in task_kwargs["aero"]

        # do something about provenance here
        response = requests.post(
            f"{CONF.server_url}/prov/new",
            headers=aero_headers,
            verify=False,
            data=json.dumps(task_kwargs),
        )

        assert response.status_code == 200, response.content
        responses.append(response.json())
    return responses


if __name__ == "__main__":  # pragma: no cover
    with open("set_flow_uuids.sh", "w+") as f:
        f.write(f"export FLOW_DOWNLOAD={register_function(download)}\n")
        f.write(f"export FLOW_DB_COMMIT={register_function(database_commit)}\n")
        f.write(f"export FLOW_ANALYSIS_VER={register_function(get_versions)}\n")
        f.write(f"export FLOW_ANALYSIS_COMMIT={register_function(commit_analysis)}\n")
