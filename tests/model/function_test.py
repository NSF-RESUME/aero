from uuid import uuid4

from aero.models.function import create_function


def test_create(session, flow):
    uuid = uuid4()
    func = create_function(session=session, uuid=uuid)
    assert func.flows == []
    assert func.id == uuid

    uuid = uuid4()
    func = create_function(session=session, uuid=uuid, flows=[flow])
    assert func.id == uuid
    assert len(func.flows) == 1
    assert func.flows[0] == flow
