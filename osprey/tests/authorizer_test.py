from globus_sdk import NativeAppAuthClient

from osprey.server.lib.globus_auth import authenticate
from osprey.server.lib.globus_auth import _CLIENT_ID
from osprey.server.lib.globus_auth import _TIMER_CLIENT_UUID


def test_authenticate():
    client = NativeAppAuthClient(client_id=_CLIENT_ID)
    _TIMER_SCOPE = f"https://auth.globus.org/scopes/{_TIMER_CLIENT_UUID}/timer"
    authenticate(client, _TIMER_SCOPE)
