# from globus_sdk import AccessTokenAuthorizer
from globus_sdk import ClientCredentialsAuthorizer
from globus_sdk import ConfidentialAppAuthClient

from aero.config import Config


def get_authorizer(scopes) -> ClientCredentialsAuthorizer:
    confidential_client = ConfidentialAppAuthClient(
        client_id=Config.PORTAL_CLIENT_ID, client_secret=Config.PORTAL_CLIENT_SECRET
    )
    authorizer = ClientCredentialsAuthorizer(
        confidential_client=confidential_client, scopes=scopes
    )
    return authorizer
