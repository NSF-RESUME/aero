"""

NOTE:

1. Stop download if its the same file
2. Direct download using HTTPS using gcs
3. Work on authentication
    i) Use Funcx credentials to register all functions
    ii) Avoid using sudershan@uchicago.edu identity for all globus services

"""
from aero.server.lib.globus_compute import register_function


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

    from dsaas_client.config import CONF
    from dsaas_client.utils import load_tokens

    if "temp_dir" in kwargs:
        TEMP_DIR = kwargs["temp_dir"]
    else:
        TEMP_DIR = pathlib.Path.home() / "aero"
        kwargs["temp_dir"] = str(TEMP_DIR)

    tokens = load_tokens()
    auth_token = tokens[CONF.portal_client_id]["refresh_token"]

    headers = {"Authorization": f"Bearer {auth_token}"}

    response = requests.get(
        f'{CONF.server_url}/source/{kwargs["source_id"]}', headers=headers, verify=False
    )
    source = response.json()

    response = requests.get(source["url"])
    content_type = response.headers["content-type"]
    ext = guess_extension(content_type.split(";")[0])

    bn = str(uuid.uuid4())
    fn = Path(TEMP_DIR, bn)

    TEMP_DIR.mkdir(exist_ok=True, parents=True)

    with open(fn, "w+") as f:
        f.write(response.content.decode("utf-8"))

    kwargs["file"] = str(fn)
    kwargs["file_bn"] = bn
    kwargs["file_format"] = ext
    kwargs["checksum"] = hashlib.md5(response.content).hexdigest()
    kwargs["size"] = fn.stat().st_size
    kwargs["download"] = True

    return args, kwargs


def user_function_wrapper(*args, **kwargs):
    import requests

    from dsaas_client.config import CONF
    from dsaas_client.utils import load_tokens

    from aero.server.lib.error import ServiceError, CUSTOM_FUNCTION_ERROR
    from aero.server.lib.globus_compute import execute_function

    tokens = load_tokens()
    auth_token = tokens[CONF.portal_client_id]["refresh_token"]
    headers = {"Authorization": f"Bearer {auth_token}"}

    source_id = kwargs["source_id"]

    response = requests.get(f"{CONF.server_url}/source/{source_id}", headers=headers)

    assert response.status_code == 200, response.content
    source = response.json()

    # Verifier
    if source["verifier"] is not None:
        try:
            result = execute_function(
                source["verifier"], source["user_endpoint"], *args, **kwargs
            )
            if result is not None:
                args, kwargs = result
        except Exception:
            raise ServiceError(CUSTOM_FUNCTION_ERROR, "Verifier failed")

    # Modifier
    if source["modifier"] is not None:
        try:
            result = execute_function(
                source["modifier"], source["user_endpoint"], *args, **kwargs
            )

            if result is not None:
                args, kwargs = result
        except Exception as e:
            raise ServiceError(CUSTOM_FUNCTION_ERROR, f"Modifier failed: {e}")

    # TODO: check if data has changed

    return args, kwargs


def database_commit(*args, **kwargs):
    import json
    import pathlib
    import requests
    from dsaas_client.config import CONF
    from dsaas_client.utils import load_tokens

    tokens = load_tokens()

    auth_token = tokens[CONF.portal_client_id]["refresh_token"]
    aero_headers = {"Authorization": f"Bearer {auth_token}"}

    source_id = kwargs["source_id"]
    file_bn = kwargs["file_bn"]

    # get source
    response = requests.get(
        f"{CONF.server_url}/source/{source_id}", headers=aero_headers, verify=False
    )
    source = response.json()

    gcs_url = source["collection_url"]
    gcs_id = source["collection_uuid"]

    transfer_token = tokens[gcs_id]["access_token"]

    headers = {"Authorization": f"Bearer {transfer_token}"}

    with open(kwargs["file"], "r") as f:
        data = f.read()

    # save data to GCS
    response = requests.put(f"{gcs_url}/{file_bn}", headers=headers, data=data)

    assert response.status_code == 200, response.json()

    aero_headers["Content-type"] = "application/json"

    # add new version
    response = requests.post(
        f"{CONF.server_url}source/{source_id}/new-version",
        headers=aero_headers,
        data=json.dumps(
            {
                "file": kwargs["file_bn"],
                "file_format": kwargs["file_format"],
                "checksum": kwargs["checksum"],
                "size": kwargs["size"],
            }
        ),
    )

    pathlib.Path(kwargs["file"]).unlink()
    assert response.status_code == 200, response.json()
    return response.json()


if __name__ == "__main__":
    with open("set_flow_uuids.sh", "w+") as f:
        f.write(f"export FLOW_DOWNLOAD={register_function(download)}\n")
        f.write(f"export FLOW_DB_COMMIT={register_function(database_commit)}\n")
        f.write(f"export FLOW_USER_COMMIT={register_function(user_function_wrapper)}\n")
