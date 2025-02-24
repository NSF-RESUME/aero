from aero.models.tag import create_tag


def test_create(session):
    name = "test_tag"
    tag = create_tag(session, name=name)
    assert tag.id is not None
    assert tag.name == name
    assert tag.data == []
