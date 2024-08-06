from enum import IntEnum

from globus_sdk import SpecificFlowClient
from globus_sdk.scopes.data import TimerScopes

_TIMER_CLIENT_UUID: str = "524230d7-ea86-4a52-8312-86065a9e0417"


class FlowEnum(IntEnum):
    NONE = -1
    VERIFY_OR_MODIFY = 0
    VERIFY_AND_MODIFY = 0
    USER_FLOW = 1


# PERMANENT
# TODO: Remove None as it is unnecessary
FLOW_IDS = {
    FlowEnum.NONE: "6f04c927-d319-41ae-a027-561329e4c2d1",
    FlowEnum.VERIFY_OR_MODIFY: "6f04c927-d319-41ae-a027-561329e4c2d1",
    FlowEnum.USER_FLOW: "0d8ace1a-d583-4f65-834e-4e1e1f450ecc",
}


def _flow_scopes():
    timer_scope = TimerScopes.make_mutable("timer")
    scopes = [timer_scope]
    # assert False, flows_scope
    for flow_id in FLOW_IDS.values():
        sfc = SpecificFlowClient(flow_id=flow_id)
        specific_flow_scope_name = f"flow_{flow_id.replace('-', '_')}_user"
        specific_flow_scope = sfc.scopes.url_scope_string(specific_flow_scope_name)
        scopes.append(sfc.scopes.user)
        timer_scope.add_dependency(specific_flow_scope)

    return scopes
