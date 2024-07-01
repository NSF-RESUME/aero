import globus_sdk

import osprey.server.lib.globus_search as gs
from osprey.server.config import Config


def load_auth_client():
    """Create a Globus Auth client from config info"""
    return globus_sdk.ConfidentialAppAuthClient(
        Config.PORTAL_CLIENT_ID, Config.PORTAL_CLIENT_SECRET
    )


def get_token(header):
    return header.split(" ")[1].strip()


def get_search_client():
    return gs.DSaaSSearchClient(Config.SEARCH_INDEX)
