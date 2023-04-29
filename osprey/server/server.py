"""Flask server implementation."""
import pickle

from flask import Flask
from flask import request

from osprey.server.scraper import available_databases
from osprey.server.proxies import url_proxies

app = Flask(__name__)


@app.route("/osprey/api/v1.0/proxies", methods=["GET"])
def get_proxies() -> bytes:
    """REST request to return proxy/ies to the user.
    
    Returns (bytes):
        The pickled dictionary of all proxies or a single pickled proxy if \
            database name to return is provided.
    """
    available_databases()
    if request.data != b"":
        data = pickle.dumps(url_proxies[str(request.data, "utf-8")][-1])
    else:
        data = pickle.dumps(url_proxies)
    return data


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
