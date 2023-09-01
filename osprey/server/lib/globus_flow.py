import json, os
from enum import IntEnum

from globus_sdk import RefreshTokenAuthorizer
from globus_sdk import NativeAppAuthClient
from globus_sdk import SpecificFlowClient
from globus_sdk import TimerClient
from globus_sdk.scopes.data import TimerScopes
from osprey.server.lib.globus_auth import create_token_file, TOKENS_FILE, _CLIENT_ID

class FlowEnum(IntEnum):
    NONE              = 0
    VERIFY_OR_MODIFY  = 1
    VERIFY_AND_MODIFY = 1

# PERMANENT
FLOW_IDS = {
    FlowEnum.NONE: 'ad25e819-ec70-4d30-aaad-a828447da332',
    FlowEnum.VERIFY_OR_MODIFY: 'b54d0c7f-cb37-4332-a17f-7cf80b9afb81'
}

def create_context(flow_id):
    sfc = SpecificFlowClient(flow_id=flow_id)
    specific_flow_scope_name = f"flow_{flow_id.replace('-', '_')}_user"
    specific_flow_scope = sfc.scopes.url_scope_string(specific_flow_scope_name)
    client = NativeAppAuthClient(client_id=_CLIENT_ID)
    return client, specific_flow_scope

def all_scopes_for_timer():
    timer_scope = TimerScopes.make_mutable("timer")
    for flow_id in FLOW_IDS.values():
        sfc = SpecificFlowClient(flow_id=flow_id)
        specific_flow_scope_name = f"flow_{flow_id.replace('-', '_')}_user"
        specific_flow_scope = sfc.scopes.url_scope_string(specific_flow_scope_name)
        timer_scope.add_dependency(specific_flow_scope)

    return timer_scope

def create_authorizer(flow_id):
    client, specific_flow_scope = create_context(flow_id)
    if os.path.exists(TOKENS_FILE):
        with open(TOKENS_FILE) as f:
            tokens = json.load(f)
        timer_refresh_token = tokens["refresh_token"]
        authorizer = RefreshTokenAuthorizer(timer_refresh_token, client)
    else:
        authorizer = create_token_file(client, all_scopes_for_timer())
    return authorizer, specific_flow_scope

def create_client(flow_id):
    authorizer, _ = create_authorizer(flow_id)
    return TimerClient(authorizer=authorizer, app_name="osprey-prototype")

def get_job(flow_id, job_id):
    timer_client = create_client(flow_id)
    return timer_client.get_job(job_id)