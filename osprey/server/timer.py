import datetime
import json
import os

from globus_compute_sdk import Client
from globus_sdk import AccessTokenAuthorizer
from globus_sdk import RefreshTokenAuthorizer
from globus_sdk import NativeAppAuthClient
from globus_sdk import SpecificFlowClient
from globus_sdk import TimerClient
from globus_sdk import TimerJob
from globus_sdk.scopes.data import TimerScopes
from globus_sdk.utils import slash_join


OSPREY_DIR = os.path.join(os.path.expanduser('~'), '.local/share/osprey')
TOKENS_FILE = os.path.join(OSPREY_DIR, 'tokens.json')

_CLIENT_ID: str = "c78511ef-8cf7-4802-a7e1-7d56e27b1bf8"
_FLOW_UUID: str = "6c2f7e41-00d0-4dc7-8c2b-2daea17edf2e"
_FUNCTION_UUID: str = "439b3807-20b7-469f-8680-586c57bb3817"
_ENDPOINT_UUID: str = "73e17ae1-03f6-4c3c-9d54-18035e617642"
_TIMER_CLIENT_UUID: str = "524230d7-ea86-4a52-8312-86065a9e0417"
_REDIRECT_URI = "https://auth.globus.org/v2/web/auth-code"


def authenticate(client: NativeAppAuthClient, scope: str):

    client.oauth2_start_flow(
        redirect_uri=_REDIRECT_URI, refresh_tokens=True, requested_scopes=scope
    )

    url = client.oauth2_get_authorize_url()
    print("Please visit the following url to authenticate:")
    print(url)

    auth_code = input("Enter the auth code:")
    auth_code = auth_code.strip()
    return client.oauth2_exchange_code_for_tokens(auth_code)

def set_timer():
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
        tokens = authenticate(client, scope=timer_scope)
        timer_access_token = tokens.by_resource_server[_TIMER_CLIENT_UUID]["access_token"]
        authorizer = AccessTokenAuthorizer(access_token=timer_access_token)

        with open(TOKENS_FILE, 'w+') as f:
            json.dump(tokens.by_resource_server[_TIMER_CLIENT_UUID], f)

    timer_client = TimerClient(authorizer=authorizer, app_name="osprey-prototype")

    run_input = {"endpoint": _ENDPOINT_UUID, "function": _FUNCTION_UUID}
    run_label = "Osprey prototype"

    url = slash_join(sfc.base_url, f"/flows/{_FLOW_UUID}/run")

    start = datetime.datetime.utcnow()
    interval = datetime.timedelta(days=1)
    name = "osprey-prototype-scraper"
    number_of_runs = 3

    job = TimerJob(
        callback_url=url,
        callback_body={"body": run_input, "label": run_label},
        start=start,
        interval=interval,
        stop_after_n=number_of_runs,
        name=name,
        scope=specific_flow_scope,
    )

    response = timer_client.create_job(job)
    assert response.http_status == 201
    job_id = response["job_id"]
    print(f"Response: {response}")


def scrape():
    from osprey.server.scraper import available_tables
    from osprey.server.scraper import scrape_database

    available_databases()
    scrape_database()


if __name__ == "__main__":
    os.makedirs(OSPREY_DIR, exist_ok=True)
    set_timer()
