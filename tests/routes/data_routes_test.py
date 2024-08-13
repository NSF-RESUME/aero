import json

from uuid import uuid4

import aero.models as models

ROUTE = "/osprey/api/v1.0/data"
KEYS = sorted(
    [
        "available_versions",
        "collection_url",
        "collection_uuid",
        "user_endpoint",
        "description",
        "email",
        "id",
        "vm_func",
        "name",
        "timer",
        "url",
    ]
)


def test_create_source(client):
    headers = {"Content-Type": "application/json"}
    data = {
        "name": "test",
        "url": "https://dummyjson.com/products/1",
        "email": "vhayot@uchicago.edu",
        "collection_uuid": str(uuid4()),
        "collection_url": "https://1234",
        "description": "this data is x",
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
    assert all([sorted(r.keys()) == KEYS for r in resp_data]) is True, sorted(
        resp_data[0].keys()
    )


def test_get_source(client, mocker):
    data_id = models.data.Data.query.first().id
    response = client.get(f"{ROUTE}/{data_id}", follow_redirects=True)
    assert sorted(response.json.keys()) == KEYS

    data_id = uuid4()
    response = client.get(f"{ROUTE}/{data_id}", follow_redirects=True)
    assert response.json["code"] == 404


def test_list_versions(client, mocker):
    data_id = models.data.Data.query.first().id
    response = client.get(f"{ROUTE}/{data_id}/versions", follow_redirects=True)
    assert response.status_code == 200

    data_id = uuid4()
    response = client.get(f"{ROUTE}/{data_id}/versions", follow_redirects=True)
    assert response.status_code == 404


def test_new_verion(client, mocker):
    # Check how many versions exist
    data_id = models.data.Data.query.first().id
    response = client.get(f"{ROUTE}/{data_id}/versions", follow_redirects=True)
    original_versions = len(response.json)

    headers = {"Content-Type": "application/json"}

    # Add new version
    data = json.dumps({"file": "fn", "file_format": "ff", "checksum": "10", "size": 4})
    response = client.post(
        f"{ROUTE}/{data_id}/new-version",
        data=data,
        headers=headers,
        follow_redirects=True,
    )
    assert response.status_code == 200, response.json
    assert (
        len(models.data.Data.query.filter_by(id=data_id).first().versions)
        == original_versions + 1
    )

    # attempt to dump the same data again
    response = client.post(
        f"{ROUTE}/{data_id}/new-version",
        data=data,
        headers=headers,
        follow_redirects=True,
    )
    assert response.status_code == 200, response.json
    assert (
        len(models.data.Data.query.filter_by(id=data_id).first().versions)
        == original_versions + 1
    )

    data_id = uuid4()
    # test when source does not exist
    response = client.post(
        f"{ROUTE}/{data_id}/new-version",
        data=data,
        headers=headers,
        follow_redirects=True,
    )
    assert response.status_code == 404


def test_grap_file(client, mocker):
    data_id = models.data.Data.query.first().id
    response = client.get(f"{ROUTE}/{data_id}/file", follow_redirects=True)
    assert response.json is not None

    data_id = uuid4()
    response = client.get(f"{ROUTE}/{data_id}/file", follow_redirects=True)
    assert response.status_code == 404

    s: models.data.Data = models.data.Data(
        name="newsource",
        url="test",
        collection_uuid=str(uuid4()),
        collection_url="https://1234",
        description="test",
    )

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
