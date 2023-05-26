"""Database scraper implementation."""
import datetime
import json
import hashlib
import os
import requests

from typing import NamedTuple
from unittest import mock
from osprey.server.proxies import proxify


class Metadata(NamedTuple):
    name: str
    url: str
    checksum: str
    last_modif: str
    version: int


_avail_data: dict[str, list[Metadata]] = {}


# TODO: store in actual databases
def table_sources() -> None:
    """Determine which source tables should be scraped."""
    path = "osprey/server/databases"
    for fn in os.listdir(path):
        if fn not in _avail_data:
            with open(os.path.join(path, fn), "r") as f:
                metadata = json.load(f)
            _avail_data[fn] = [
                Metadata(metadata["name"], metadata["url"], None, None, 0)
            ]


def get_tables() -> None:
    """Provided list of all source tables, scrape and proxy data."""
    for key, v in _avail_data.items():
        m = v[-1]  # Get last update in list of files
        req = requests.get(m.url)
        data = req.json()
        new_hash = hashlib.md5(json.dumps(data).encode("utf-8")).hexdigest()
        last_modif = req.headers["Last-Modified"]

        if new_hash == m.checksum:
            return

        if m.checksum is None:
            _avail_data[key] = [Metadata(m.name, m.url, new_hash, last_modif, 1)]
        else:
            _avail_data[key].append(
                Metadata(m.name, m.url, new_hash, last_modif, m["version"] + 1)
            )

        validate()
        proxify(m.name, data)


def validate() -> None:
    """Validate the recently modified data to ensure it meets standards"""
    pass
