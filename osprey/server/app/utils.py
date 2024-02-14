import globus_sdk

from osprey.server.config import Config


def load_auth_client():
    """Create a Globus Auth client from config info"""
    print("HELOOO")
    print(Config.PORTAL_CLIENT_ID, Config.PORTAL_CLIENT_SECRET)
    return globus_sdk.ConfidentialAppAuthClient(
        Config.PORTAL_CLIENT_ID, Config.PORTAL_CLIENT_SECRET
    )


def get_token(header):
    return header.split(" ")[1].strip()
