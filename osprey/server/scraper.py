"""Database scraper implementation."""
import json
import os
import requests

from osprey.server.proxies import proxify

_avail_data: dict[str, tuple[str, str]] = {}


# TODO: store in actual databases
def available_databases() -> None:
    """Determine which databases should be scraped."""
    path = "osprey/server/databases"
    for fn in os.listdir(path):
        if fn not in _avail_data:
            with open(os.path.join(path, fn), "r") as f:
                metadata = json.load(f)
            _avail_data[fn] = (metadata["name"], metadata["url"])


def scrape_database() -> None:
    """Provided list of all databases, scrape and proxy data."""
    for name, url in _avail_data.values():
        req = requests.get(url)
        proxify(name, req.json())


available_databases()
scrape_database()
