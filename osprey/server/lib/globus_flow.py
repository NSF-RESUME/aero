from enum import IntEnum
from typing import Literal

from globus_sdk import RefreshTokenAuthorizer
from globus_sdk import NativeAppAuthClient
from globus_sdk import SpecificFlowClient
from globus_sdk import TimerClient
from globus_sdk.scopes.data import TimerScopes

from osprey.server.lib.globus_auth import _CLIENT_ID
from osprey.server.lib.globus_auth import create_token_file
from osprey.server.lib.globus_auth import _TIMER_CLIENT_UUID
from osprey.server.lib.globus_auth import TOKENS_FILE


class FlowEnum(IntEnum):
    NONE = 0
    VERIFY_OR_MODIFY = 1
    VERIFY_AND_MODIFY = 1
    USER_FLOW = 2


# PERMANENT
# TODO: Remove None as it is unnecessary
FLOW_IDS = {
    FlowEnum.NONE: "6f04c927-d319-41ae-a027-561329e4c2d1",
    FlowEnum.VERIFY_OR_MODIFY: "6f04c927-d319-41ae-a027-561329e4c2d1",
    FlowEnum.USER_FLOW: "0d8ace1a-d583-4f65-834e-4e1e1f450ecc",
}


def create_context(flow_id):
    sfc = SpecificFlowClient(flow_id=flow_id)
    specific_flow_scope_name = f"flow_{flow_id.replace('-', '_')}_user"
    specific_flow_scope = sfc.scopes.url_scope_string(specific_flow_scope_name)
    client = NativeAppAuthClient(client_id=_CLIENT_ID)
    return client, specific_flow_scope


def all_scopes_for_flows():
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


def create_authorizer(flow_id, auth_type: Literal["flow", "timer"]):
    client, specific_flow_scope = create_context(flow_id)

    if auth_type == "timer":
        resource_server = _TIMER_CLIENT_UUID
    else:
        resource_server = flow_id

    if TOKENS_FILE.file_exists():
        tokens = TOKENS_FILE.get_token_data(resource_server)
        refresh_token = tokens["refresh_token"]
        authorizer = RefreshTokenAuthorizer(refresh_token, client)
    else:
        authorizer = create_token_file(
            client, all_scopes_for_flows(), auth_type=auth_type, fid=flow_id
        )
    return authorizer, specific_flow_scope


def create_client(flow_id):
    authorizer, _ = create_authorizer(flow_id, "timer")
    return TimerClient(authorizer=authorizer, app_name="osprey-prototype")


def get_job(flow_id, job_id):
    timer_client = create_client(flow_id)
    return timer_client.get_job(job_id)
