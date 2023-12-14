import json

from pathlib import Path
from random import randint

from osprey.worker.models.source import Source
from osprey.tests.server.conftest import db

ROUTE = "/osprey/api/v1.0/source"
SOURCE_KEYS = sorted(
    [
        "available_versions",
        "description",
        "email",
        "id",
        "modifier",
        "name",
        "timer",
        "url",
        "verifier",
    ]
)
GCS_DIR = Path("/dsaas_storage")
TEMP_DIR = Path(GCS_DIR, "temp")
SOURCE_DIR = Path(GCS_DIR, "source")

TEMP_DIR.mkdir(parents=True, exist_ok=True)
SOURCE_DIR.mkdir(parents=True, exist_ok=True)


def test_create_source(client, mocker):
    mocker.patch("osprey.server.models.source.Source._start_timer_flow")
    headers = {"Content-Type": "application/json"}
    data = {
        "name": "test",
        "url": "https://dummyjson.com/products/1",
        "email": "vhayot@uchicago.edu",
    }
    response = client.post(ROUTE, json=data, headers=headers, follow_redirects=True)
    resp_dict = response.json

    assert resp_dict["name"] == data["name"]
    assert resp_dict["url"] == data["url"]
    assert resp_dict["email"] == data["email"]


def test_list_sources(client):
    response = client.get(ROUTE, follow_redirects=True)
    resp_data = response.json

    assert len(resp_data) >= 1  # should have at least a single element
    assert all([sorted(r.keys()) == SOURCE_KEYS for r in resp_data]) is True


def test_get_source(client):
    response = client.get(f"{ROUTE}/1", follow_redirects=True)
    assert sorted(response.json.keys()) == SOURCE_KEYS

    response = client.get(f"{ROUTE}/100", follow_redirects=True)
    assert response.json["code"] == 404


def test_list_versions(client):
    # Add new version
    response = client.get(f"{ROUTE}/1/versions", follow_redirects=True)
    original_versions = len(response.json)

    fn1 = "list_version_test1"
    data = {"hello": f"world{randint(0, 100)}{randint(0, 100)}{randint(0, 100)}"}
    with open(Path(TEMP_DIR, fn1), "w+") as f:
        json.dump(data, f)

    db.session.get(Source, 1).add_new_version(fn1, "json")
    assert len(db.session.get(Source, 1).versions) == original_versions + 1

    # attempt to dump the same data again
    with open(Path(TEMP_DIR, fn1), "w+") as f:
        json.dump(data, f)
    db.session.get(Source, 1).add_new_version(fn1, "json")
    assert len(db.session.get(Source, 1).versions) == original_versions + 1

    # test if version doesn't exist
    response = client.get(f"{ROUTE}/100/versions", follow_redirects=True)
    assert response.json["code"] == 404


def test_grap_file(client):
    response = client.get(f"{ROUTE}/1/file", follow_redirects=True)
    assert response.json is not None
