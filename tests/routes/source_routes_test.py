import json

import osprey.server.models as models

ROUTE = "/osprey/api/v1.0/source"
SOURCE_KEYS = sorted(
    [
        "available_versions",
        "collection_url",
        "collection_uuid",
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


def test_create_source(client):
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

    # Create source without url
    data = {
        "name": "test",
        "email": "vhayot@uchicago.edu",
    }

    response = client.post(ROUTE, json=data, headers=headers, follow_redirects=True)
    assert response.status_code != 200


def test_list_sources(client, mocker):
    response = client.get(ROUTE, follow_redirects=True)
    resp_data = response.json

    assert len(resp_data) >= 1  # should have at least a single element
    assert all([sorted(r.keys()) == SOURCE_KEYS for r in resp_data]) is True


def test_get_source(client, mocker):
    response = client.get(f"{ROUTE}/1", follow_redirects=True)
    assert sorted(response.json.keys()) == SOURCE_KEYS

    response = client.get(f"{ROUTE}/100", follow_redirects=True)
    assert response.json["code"] == 404


def test_list_versions(client, mocker):
    response = client.get(f"{ROUTE}/1/versions", follow_redirects=True)
    assert response.status_code == 200

    response = client.get(f"{ROUTE}/1000/versions", follow_redirects=True)
    assert response.status_code == 404


def test_new_verion(client, mocker):
    # Check how many versions exist
    response = client.get(f"{ROUTE}/1/versions", follow_redirects=True)
    original_versions = len(response.json)

    headers = {"Content-Type": "application/json"}

    # Add new version
    data = json.dumps({"file": "fn", "file_format": "ff", "checksum": "10", "size": 4})
    response = client.post(
        f"{ROUTE}/1/new-version", data=data, headers=headers, follow_redirects=True
    )
    assert response.status_code == 200, response.json
    assert (
        len(models.source.Source.query.filter_by(id=1).first().versions)
        == original_versions + 1
    )

    # attempt to dump the same data again
    response = client.post(
        f"{ROUTE}/1/new-version", data=data, headers=headers, follow_redirects=True
    )
    assert response.status_code == 200, response.json
    assert (
        len(models.source.Source.query.filter_by(id=1).first().versions)
        == original_versions + 1
    )

    # test when source does not exist
    response = client.post(
        f"{ROUTE}/1000/new-version", data=data, headers=headers, follow_redirects=True
    )
    assert response.status_code == 404


def test_grap_file(client, mocker):
    response = client.get(f"{ROUTE}/1/file", follow_redirects=True)
    assert response.json is not None

    response = client.get(f"{ROUTE}/500/file", follow_redirects=True)
    assert response.status_code == 404

    s: models.source.Source = models.source.Source(name="newsource", url="test")

    response = client.get(f"{ROUTE}/{s.id}/file", follow_redirects=True)
    assert response.status_code

    # get specific version
    headers = {
        "Content-Type": "application/json",
    }
    response = client.get(
        f"{ROUTE}/{s.id}/file?version=1", headers=headers, follow_redirects=True
    )
    assert response.status_code
