import datetime, json, os, sys

from osprey.server.lib.globus_auth import create_token_file, TOKENS_FILE, _CLIENT_ID

from globus_sdk import RefreshTokenAuthorizer
from globus_sdk import NativeAppAuthClient
from globus_sdk import SpecificFlowClient
from globus_sdk import TimerClient
from globus_sdk import TimerJob
from globus_sdk.scopes.data import TimerScopes
from globus_sdk.utils import slash_join

# Permanent
_FLOW_UUID: str = "6c2f7e41-00d0-4dc7-8c2b-2daea17edf2e"

def set_timer(func_uuid: str, endpoint_uuid: str) -> None:
    """Set a Globus Timer for daily retrieval of updated tables from sources.

    Arguments:
        func_uuid: The Globus Compute registered function UUID.
    """
    sfc = SpecificFlowClient(flow_id=_FLOW_UUID)
    specific_flow_scope_name = f"flow_{_FLOW_UUID.replace('-', '_')}_user"
    specific_flow_scope = sfc.scopes.url_scope_string(specific_flow_scope_name)
    timer_scope = TimerScopes.make_mutable("timer")
    timer_scope.add_dependency(specific_flow_scope)

    client = NativeAppAuthClient(client_id=_CLIENT_ID)

    if os.path.exists(TOKENS_FILE):
        with open(TOKENS_FILE) as f:
            tokens = json.load(f)
        timer_refresh_token = tokens["refresh_token"]
        authorizer = RefreshTokenAuthorizer(timer_refresh_token, client)
    else:
        authorizer = create_token_file(client, timer_scope)

    timer_client = TimerClient(authorizer=authorizer, app_name="osprey-prototype")

    run_input = {"endpoint": endpoint_uuid, "function": func_uuid}
    run_label = "Osprey prototype"

    url = slash_join(sfc.base_url, f"/flows/{_FLOW_UUID}/run")

    start = datetime.datetime.utcnow()
    interval = datetime.timedelta(minutes=1.5)
    name = "osprey-prototype-scraper"

    job = TimerJob(
        callback_url=url,
        callback_body={"body": run_input, "label": run_label},
        start=start,
        interval=interval,
        name=name,
        scope=specific_flow_scope,
    )

    response = timer_client.create_job(job)
    assert response.http_status == 201
    job_id = response["job_id"]
    print(f"Response: {response}")

def scrape():
    return 0

if __name__ == "__main__":
    if(len(sys.argv) != 2):
        print("Usage: python timer.py <endpoint_id>")
        exit()

    endpoint_uuid = sys.argv[1]
    
    set_timer(func_uuid, endpoint_uuid)
