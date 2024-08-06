ROUTE = "/osprey/api/v1.0/output/"
OUTPUT_KEYS = sorted(
    [
        "available_versions",
        "collection_uuid",
        "description",
        "id",
        "name",
        "url",
        "provenance_id",
    ]
)


def test_create_output_file(client):
    headers = {"Content-Type": "application/json"}
    data = {
        "filename": "fn",
        "checksum": "9",
        "url": "www.test.com",
        "name": "name",
        "collection_uuid": "1234",
    }

    response = client.post(
        f"{ROUTE}/new", json=data, headers=headers, follow_redirects=True
    )
    assert response.status_code == 200

    # Rerun with description in data
    data["description"] = "some description"
    response = client.post(
        f"{ROUTE}/new", json=data, headers=headers, follow_redirects=True
    )
    assert response.status_code == 200


def test_show_output(client):
    headers = {"Content-Type": "application/json"}
    response = client.get(ROUTE, headers=headers, follow_redirects=True)
    assert response.status_code == 200
    assert sorted(response.json[0].keys()) == OUTPUT_KEYS, response.json
