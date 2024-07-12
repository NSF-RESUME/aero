# from globus_sdk import AccessTokenAuthorizer
from globus_sdk import ClientCredentialsAuthorizer
from globus_sdk import ConfidentialAppAuthClient

from osprey.server.config import Config

# TODO: Move outside of server dir
# Permanent
# OSPREY_DIR = os.path.join(os.path.expanduser("~"), ".local/share/osprey")
# TODO: Change this
# OSPREY_DIR = "/app/osprey/server/"
# TOKENS_FILE = SimpleJSONFileAdapter(os.path.join(OSPREY_DIR, "tokens.json"))

# _REDIRECT_URI = "https://auth.globus.org/v2/web/auth-code"
# _CLIENT_ID: str = "c78511ef-8cf7-4802-a7e1-7d56e27b1bf8"


# def authenticate(client: NativeAppAuthClient, scope: str):
#     """Perform Globus Authentication."""

#     # assert False, scope
#     client.oauth2_start_flow(
#         redirect_uri=_REDIRECT_URI, refresh_tokens=True, requested_scopes=scope
#     )

#     url = client.oauth2_orize_url()
#     print("Please visit the following url to authenticate:")
#     print(url)

#     auth_code = input("Enter the auth code:")
#     auth_code = auth_code.strip()
#     return client.oauth2_exchange_code_for_tokens(auth_code)


# def create_token_file(
#     client: NativeAppAuthClient,
#     scope: str | None = None,
#     auth_type: Literal["flows", "timer", "search"] = "flows",
#     fid: str = None,
# ) -> AccessTokenAuthorizer:
#     os.makedirs(OSPREY_DIR, exist_ok=True)
#     tokens = authenticate(client, scope)
#     TOKENS_FILE.store(tokens)

#     if auth_type == "flows":
#         assert fid is not None
#         flows_access_token = tokens.by_resource_server[fid]["access_token"]
#         authorizer = AccessTokenAuthorizer(access_token=flows_access_token)

#     elif auth_type == "timer":
#         timer_access_token = tokens.by_resource_server[_TIMER_CLIENT_UUID][
#             "access_token"
#         ]
#         authorizer = AccessTokenAuthorizer(access_token=timer_access_token)

#     else:
#         search_access_token = tokens.by_resource_server[SearchClient.resource_server][
#             "access_token"
#         ]
#         authorizer = AccessTokenAuthorizer(access_token=search_access_token)

#     return authorizer


def get_authorizer(scopes) -> ClientCredentialsAuthorizer:
    confidential_client = ConfidentialAppAuthClient(
        client_id=Config.PORTAL_CLIENT_ID, client_secret=Config.PORTAL_CLIENT_SECRET
    )
    authorizer = ClientCredentialsAuthorizer(
        confidential_client=confidential_client, scopes=scopes
    )
    return authorizer


# if __name__ == "__main__":

#     # if not os.path.exists(TOKENS_FILE):
#     #     client = NativeAppAuthClient(client_id=_CLIENT_ID)
#     #     _TIMER_SCOPE = f"https://auth.globus.org/scopes/{_TIMER_CLIENT_UUID}/timer"
#     #     authenticate(client, _TIMER_SCOPE)
