import aero.models
import aero.models.tag


def test_create(session):
    name = "test_tag"
    tag = aero.models.tag.create_tag(session, name=name)
    assert tag.id is not None
    assert tag.name == name
    assert tag.data == []
