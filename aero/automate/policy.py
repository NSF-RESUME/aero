from typing import TypeAlias

from globus_sdk import AuthClient
from globus_sdk import SpecificFlowClient

from aero.globus.auth import get_authorizer
from aero.globus.utils import FLOW_IDS
from aero.globus.utils import FlowEnum
from aero.globus.utils import _flow_scopes

JSON: TypeAlias = dict[str, "JSON"] | list["JSON"] | str | int | float | bool | None


def run_flow(
    endpoint_uuid: str,
    function_uuid: str,
    pull_function_uuid: str,
    commit_function_uuid: str,
    tasks: JSON,
    email: str | None,
):
    flow_id = FLOW_IDS[FlowEnum.USER_FLOW]

    authorizer = get_authorizer(scopes=_flow_scopes(flow_id=flow_id))
    sfc = SpecificFlowClient(flow_id=flow_id, authorizer=authorizer)
    monitors = []

    if isinstance(tasks, dict):
        tasks = [tasks]

    if email is not None:
        ac = AuthClient(authorizer=authorizer)
        user_uuid = ac.get_identities(usernames=email)["identities"][0]["id"]
        monitors.append(user_uuid)

    run_input = {
        "endpoint": endpoint_uuid,
        "version_function": pull_function_uuid,
        "commit_function": commit_function_uuid,
        "function": function_uuid,
        "tasks": tasks,
    }
    response = sfc.run_flow(
        body=run_input,
        label="AERO Demo | User flow",
        run_managers=monitors,
    )
    assert response.http_status == 201
