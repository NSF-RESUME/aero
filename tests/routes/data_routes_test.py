from uuid import uuid4


ROUTE = "/data"
KEYS = sorted(
    [
        "collection_url",
        "collection_uuid",
        "description",
        "id",
        "name",
        "url",
    ]
)


def test_list_data(client, mocker, data):
    response = client.get(ROUTE, follow_redirects=True)
    resp_data = response.json()

    assert response.status_code == 200
    assert len(resp_data) >= 1  # should have at least a single element
    assert all([sorted(r.keys()) == KEYS for r in resp_data]) is True, sorted(
        resp_data[0].keys()
    )


def test_get_data(client, mocker, data):
    response = client.get(f"{ROUTE}/{data.id}", follow_redirects=True)
    assert response.status_code == 200
    assert sorted(response.json().keys()) == KEYS, response.json()

    data_id = uuid4()
    response = client.get(f"{ROUTE}/{data_id}", follow_redirects=True)
    assert response.status_code == 404


def test_list_versions(client, mocker, data):
    data_id = data.id
    response = client.get(f"{ROUTE}/{data_id}/versions", follow_redirects=True)
    assert response.status_code == 200
    version = dict(data.versions[0])
    resp_data = response.json()
    assert len(resp_data) == 1
    assert resp_data[0]["id"] == str(version["id"])
    assert sorted(resp_data[0].keys()) == sorted(version.keys())

    data_id = uuid4()
    response = client.get(f"{ROUTE}/{data_id}/versions", follow_redirects=True)
    assert response.status_code == 404


def test_get_latest(client, mocker, data, noversion_data):
    data_id = data.id
    response = client.get(f"{ROUTE}/{data_id}/latest", follow_redirects=True)
    assert response.status_code == 200
    version = dict(data.versions[0])
    resp_data = response.json()
    assert resp_data["id"] == str(version["id"])
    assert sorted(resp_data.keys()) == sorted(version.keys())

    data_id = uuid4()
    response = client.get(f"{ROUTE}/{data_id}/latest", follow_redirects=True)
    assert response.status_code == 404

    response = client.get(f"{ROUTE}/{noversion_data.id}/latest", follow_redirects=True)
    assert response.status_code == 404
