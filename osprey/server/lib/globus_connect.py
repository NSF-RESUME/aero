import globus_sdk, requests
from app import Config

class GlobusConnect:
    def __init__(self) -> None:
        pass

    def _authenticate(self) -> globus_sdk.ClientCredentialsAuthorizer:
        authorizer = globus_sdk.ClientCredentialsAuthorizer(
            globus_sdk.ConfidentialAppAuthClient(
                Config.CLIENT_ID,
                Config.CLIENT_SECRET
            ),
            f"urn:globus:auth:scope:{Config.GCS_ENDPOINT_ID}:manage_collections[*https://auth.globus.org/scopes/{Config.MAPPED_COLLECTION_ID}/data_access]"
        )
        return authorizer

    def _get_something(self) -> str:
        authorizer = self._authenticate()
        resp = requests.get(
            'https://' + Config.GCS_MANAGER_DOMAIN_NAME + '/api/user_credentials',
            params={'storage_gateway': Config.STORAGE_GATEWAY_ID},
            headers={'Authorization': f'Bearer {authorizer.access_token}'},
        )
