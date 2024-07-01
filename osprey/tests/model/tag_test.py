from osprey.tests.conftest import Source
from osprey.tests.conftest import Tag


def test_create(app):
    s: Source = Source(name="1", url="1", email="1")
    t: Tag = Tag(name="test", sources=[s])

    assert t.id == 1 and t.name == "test" and t.sources == [s]
    t2: Tag = Tag(name="test2", sources=[s])
    assert t2.id == 2

    s: Source = Source(name="source_with_tags", url="1", email="1", tags=[t, t2])
    assert s.tags == [t, t2]


def test_json(app):
    t: Tag = Tag.query.filter_by(name="test").first()
    t_json = t.toJSON()

    assert list(t_json.keys()) == ["id", "name"]
    assert t_json["id"] == t.id and t_json["name"] == t.name


def test_str_repr(app):
    t: Tag = Tag.query.filter_by(name="test").first()
    t_str = str(t)

    assert t_str == f"<Tag(id={t.id}, name='{t.name}')>"
