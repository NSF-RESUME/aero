"""

NOTE:

1. Stop download if its the same file
2. Direct download using HTTPS using gcs
3. Work on authentication
    i) Use Funcx credentials to register all functions
    ii) Avoid using sudershan@uchicago.edu identity for all globus services

"""

from osprey.server.lib.globus_compute import register_function


def download(*args, **kwargs):
    """Download data from user-specified repository.

    Returns:
        tuple[str, str]: Path to the data and its
            associated extension.
    """
    import hashlib
    import requests
    import uuid
    from mimetypes import guess_extension
    from pathlib import Path

    from dsaas_client.config import CONF
    from dsaas_client.utils import load_tokens
    from osprey.worker.models.utils import TEMP_DIR

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

    TEMP_DIR.mkdir(exist_ok=True)

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

    from osprey.server.lib.error import ServiceError, CUSTOM_FUNCTION_ERROR
    from osprey.server.lib.globus_compute import execute_function, get_result

    tokens = load_tokens()
    auth_token = tokens[CONF.portal_client_id]["refresh_token"]
    headers = {"Authorization": f"Bearer {auth_token}"}

    source_id = kwargs["source_id"]

    response = requests.get(
        f"{CONF.server_url}/source/{source_id}", headers=headers, verify=False
    )
    source = response.json()

    # Verifier
    if source["verifier"] is not None:
        try:
            tracker = execute_function(
                source["verifier"], source["user_endpoint"], *args, **kwargs
            )
            args, kwargs = get_result(tracker, block=True)
        except Exception:
            raise ServiceError(CUSTOM_FUNCTION_ERROR, "Verifier failed")

    # Modifier
    if source["modifier"] is not None:
        try:
            tracker = execute_function(
                source["modifier"], source["user_endpoint"], *args, **kwargs
            )
            args, kwargs = get_result(tracker, block=True)
        except Exception:
            raise ServiceError(CUSTOM_FUNCTION_ERROR, "Modifier failed")

    # TODO: check if data has changed

    return args, kwargs


def flow_db_update(sources: list[str], output_fn: str, function_uuid: str):
    from osprey.worker.models.database import Session
    from osprey.worker.models.function import Function
    from osprey.worker.models.output import Output
    from osprey.worker.models.provenance import Provenance
    from osprey.worker.models.source_version import SourceVersion

    source_ver: list = []

    # currently just gets last version
    with Session() as session:
        for s_id in sources:
            source_ver.append(
                session.query(SourceVersion)
                .filter(SourceVersion.source_id == int(s_id))
                .order_by(SourceVersion.version.desc())
                .first()
            )

        f = Function(uuid=function_uuid)
        session.add(f)

        o = Output(filename=output_fn)
        session.add(o)

        p = Provenance(function_id=f.id, derived_from=source_ver, contributed_to=[o])
        session.add(p)
        session.commit()


def database_commit(*args, **kwargs):
    import json
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

    transfer_token = tokens[gcs_id]["refresh_token"]

    headers = {"Authorization": f"Bearer {transfer_token}"}

    # save data to GCS
    response = requests.post(
        f"https://{gcs_url}/{file_bn}", headers=headers, verify=False
    )

    aero_headers["Content-type"] = "application/json"

    # add new version
    response = requests.post(
        f"{CONF.server_url}source/{source_id}/new-version",
        headers=aero_headers,
        data=json.dumps(
            {
                "file": kwargs["file"],
                "file_format": kwargs["file_format"],
                "checksum": kwargs["checksum"],
                "size": kwargs["size"],
            }
        ),
        verify=False,
    )

    return response.json()


if __name__ == "__main__":
    print("Globus Flow download", register_function(download))
    print("Globus Flow database commit", register_function(database_commit))
    print("Globus Flow user function commit", register_function(user_function_wrapper))
    print("UDF Globus Flow db commit", register_function(flow_db_update))
