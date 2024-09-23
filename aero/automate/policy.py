from typing import TypeAlias

from globus_sdk import SpecificFlowClient

from aero.config import Config
from aero.globus.auth import get_authorizer
from aero.globus.utils import FLOW_IDS
from aero.globus.utils import FlowEnum
from aero.globus.utils import _flow_scopes

JSON: TypeAlias = dict[str, "JSON"] | list["JSON"] | str | int | float | bool | None


def run_flow(endpoint_uuid: str, function_uuid: str, tasks: JSON):
    flow_id = FLOW_IDS[FlowEnum.USER_FLOW]

    authorizer = get_authorizer(scopes=_flow_scopes(flow_id=flow_id))
    sfc = SpecificFlowClient(flow_id=flow_id, authorizer=authorizer)

    if isinstance(tasks, dict):
        tasks = [tasks]

    run_input = {
        "endpoint": endpoint_uuid,
        "version_function": Config.GLOBUS_FLOW_ANALYSIS_VER_FUNC,
        "commit_function": Config.GLOBUS_FLOW_ANALYSIS_COMMIT_FUNC,
        "function": function_uuid,
        "tasks": tasks,
    }
    response = sfc.run_flow(body=run_input, label="AERO Demo | User flow")
    assert response.http_status == 201
