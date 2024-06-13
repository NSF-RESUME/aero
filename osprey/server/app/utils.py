import globus_sdk
import os

from osprey.server.config import Config
from osprey.server.lib.globus_search import DSaaSSearchClient


def load_auth_client():
    """Create a Globus Auth client from config info"""
    return globus_sdk.ConfidentialAppAuthClient(
        Config.PORTAL_CLIENT_ID, Config.PORTAL_CLIENT_SECRET
    )


def get_token(header):
    return header.split(" ")[1].strip()


SEARCH_INDEX = os.getenv("SEARCH_INDEX")
search_client = DSaaSSearchClient(SEARCH_INDEX)
