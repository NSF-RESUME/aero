from aero.config import Config
from aero.globus.client import GlobusClient

GLOBUS_CLIENT = GlobusClient(search_index=Config.SEARCH_INDEX)
