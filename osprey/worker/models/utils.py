import os
from pathlib import Path

if (test := os.getenv("DSAAS_TESTENV")) is not None and int(test) == 1:
    server_address = "localhost:5001"
else:
    server_address = "129.114.27.115:5001"

SERVER_URL = f"https://{server_address}/osprey/api/v1.0/"

TEMP_DIR = Path("/tmp/aero/")
