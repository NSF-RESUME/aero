import json

from typing import TypeAlias

from globus_sdk import SpecificFlowClient

from aero.globus.auth import get_authorizer
from aero.globus.utils import FLOW_IDS
from aero.globus.utils import FlowEnum
from aero.globus.utils import _flow_scopes

JSON: TypeAlias = dict[str, "JSON"] | list["JSON"] | str | int | float | bool | None


def run_flow(endpoint_uuid: str, function_uuid: str, tasks: JSON):
    flow_id = FLOW_IDS[FlowEnum.USER_FLOW]

    authorizer = get_authorizer(scopes=_flow_scopes())
    sfc = SpecificFlowClient(flow_id=flow_id, authorizer=authorizer)
    run_input = {
        "user_endpoint": endpoint_uuid,
        "user_function": function_uuid,
        "tasks": json.dumps(tasks),
    }
    response = sfc.run_flow(body=run_input, label="Osprey Demo | User flow")
    assert response.http_status == 201
