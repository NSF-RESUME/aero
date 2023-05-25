"""Database scraper implementation."""
import datetime
import json
import hashlib
import os
import requests

from typing import NamedTuple
from unittest import mock

from globus_compute_sdk import Client
from globus_sdk import NativeAppAuthClient
from globus_sdk import AccessTokenAuthorizer
from globus_sdk import TimerClient
from globus_sdk import TimerJob

from osprey.server.proxies import proxify


class Metadata(NamedTuple):
    name: str
    url: str
    checksum: str
    last_modif: str
    version: int


_avail_data: dict[str, list[Metadata]] = {}
_CLIENT_ID: str = 'c78511ef-8cf7-4802-a7e1-7d56e27b1bf8'
_REDIRECT_URI = 'https://auth.globus.org/v2/web/auth-code'


# TODO: store in actual databases
def available_databases() -> None:
    """Determine which databases should be scraped."""
    path = "osprey/server/databases"
    for fn in os.listdir(path):
        if fn not in _avail_data:
            with open(os.path.join(path, fn), "r") as f:
                metadata = json.load(f)
            _avail_data[fn] = [
                Metadata(metadata["name"], metadata["url"], None, None, 0)
            ]


def scrape_database() -> None:
    """Provided list of all databases, scrape and proxy data."""
    for key, v in _avail_data.items():
        m = v[-1]  # Get last update in list of files
        req = requests.get(m.url)
        data = req.json()
        new_hash = hashlib.md5(json.dumps(data).encode("utf-8")).hexdigest()
        last_modif = req.headers["Last-Modified"]

        if new_hash == m.checksum:
            return

        proxify(m.name, data)

        if m.checksum is None:
            _avail_data[key] = [Metadata(m.name, m.url, new_hash, last_modif, 1)]
        else:
            _avail_data[key].append(
                Metadata(m.name, m.url, new_hash, last_modif, m["version"] + 1)
            )

def create_action_request(endpoint_uuid, function_uuid):
    return {
            "endpoint": endpoint_uuid,
            "function": function_uuid,
           }

def authenticate():
    client = NativeAppAuthClient(client_id=_CLIENT_ID)
    client.oauth2_start_flow(
        redirect_uri=_REDIRECT_URI,
        refresh_tokens=True,
    )

    url = client.oauth2_get_authorize_url()
    print('Please visit the following url to authenticate:')
    print(url)

    auth_code = input('Enter the auth code:')
    auth_code = auth_code.strip()
    return client.oauth2_exchange_code_for_tokens(auth_code)



def set_timer():
    tokens = authenticate()
    authorizer = AccessTokenAuthorizer(access_token=tokens['access_token'])
    timer_client = TimerClient(authorizer=authorizer, app_name='osprey-prototype')

    gcc = Client()
    function_uuid = gcc.register_function(scrape)

    endpoint_uuid= "73e17ae1-03f6-4c3c-9d54-18035e617642"
    callback_url = "https://compute.actions.globus.org/run"
    ar = create_action_request(endpoint_uuid, function_uuid)
    
    job = TimerJob(callback_url, ar, start=datetime.datetime.utcnow(), interval=3, name='osprey-prototype-scraper', stop_after_n=3)
    timer_result = timer_client.create_job(job)

    print(timer_result)

def scrape():
    available_databases()
    scrape_database()

if __name__=='__main__':
    set_timer()
