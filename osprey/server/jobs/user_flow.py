import json

from typing import TypeAlias

from globus_sdk import SpecificFlowClient

from osprey.server.lib.globus_flow import create_authorizer, FLOW_IDS, FlowEnum

JSON: TypeAlias = dict[str, "JSON"] | list["JSON"] | str | int | float | bool | None


def run_flow(endpoint_uuid: str, function_uuid: str, tasks: JSON):
    flow_id = FLOW_IDS[FlowEnum.USER_FLOW]

    authorizer, specific_flow_scope = create_authorizer(flow_id, "flow")
    sfc = SpecificFlowClient(flow_id=flow_id, authorizer=authorizer)
    run_input = {
        "user_endpoint": endpoint_uuid,
        "user_function": function_uuid,
        "tasks": json.dumps(tasks),
    }
    response = sfc.run_flow(body=run_input, label="Osprey Demo | User flow")
    assert response.http_status == 201
