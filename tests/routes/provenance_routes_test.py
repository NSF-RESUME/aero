from datetime import datetime


ROUTE = "/prov"
KEYS = sorted(["id", "flow_id"])


def test_list_data(client, mocker, prov):
    response = client.get(ROUTE, follow_redirects=True)
    resp_data = response.json()

    assert response.status_code == 200
    assert len(resp_data) == 1
    assert all([sorted(r.keys()) == KEYS for r in resp_data]) is True, resp_data[0]


def test_add_record(client, data, noversion_data, flow):
    input_data = {"inpt": {"id": str(data.id), "version": len(data.versions)}}
    output_data = {
        "outpt": {
            "id": str(noversion_data.id),
            "file_bn": "bn",
            "file_format": "txt",
            "checksum": "chksm",
            "size": 123.1,
            "created_at": str(datetime.now()),
        }
    }

    flow_args = {
        "flow_id": str(flow.id),
        "input_data": input_data,
        "output_data": output_data,
    }
    response = client.post(f"{ROUTE}/new", json=flow_args, follow_redirects=True)
    resp_data = response.json()

    assert response.status_code == 200, resp_data


def test_add_record_with_no_outputs_records_the_inputs(client, session, data, flow):
    """An analysis that stores its own results still leaves a provenance trail.

    It declares no output_data, so no version is created and nothing downstream
    can chain off it -- but which input versions the run consumed is exactly what
    makes the audit trail worth having.
    """
    from sqlmodel import select

    from aero.models.provenance import Provenance

    flow_args = {
        "flow_id": str(flow.id),
        "input_data": {"inpt": {"id": str(data.id), "version": len(data.versions)}},
        "output_data": {},
    }
    response = client.post(f"{ROUTE}/new", json=flow_args, follow_redirects=True)

    assert response.status_code == 200, response.json()

    # Assert against the row: response_model=Provenance does not serialize
    # relationships, so the response body shows neither side either way.
    prov = session.exec(select(Provenance)).all()[-1]
    assert [v.data_id for v in prov.derived_from] == [data.id]
    assert prov.contributed_to == []
    assert len(data.versions) == 1, "no output means no new version anywhere"
