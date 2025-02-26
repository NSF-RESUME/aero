from uuid import uuid4

import aero.models
import aero.models.function


def test_create(session, flow):
    uuid = uuid4()
    func = aero.models.function.create_function(session=session, uuid=uuid)
    assert func.flows == []
    assert func.id == uuid

    uuid = uuid4()
    func = aero.models.function.create_function(
        session=session, uuid=uuid, flows=[flow]
    )
    assert func.id == uuid
    assert len(func.flows) == 1
    assert func.flows[0] == flow
