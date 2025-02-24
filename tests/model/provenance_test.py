from aero.models.provenance import create_provenance


def test_create_provenance(session, flow, version):
    prov = create_provenance(session=session, flow_id=flow.id, contributed_to=[version])

    assert prov.flow_id == flow.id
    assert len(prov.contributed_to) == 1
    assert prov.contributed_to[0] == version
