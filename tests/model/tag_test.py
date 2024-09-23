import aero.models as models


def test_create(app):
    collection_uuid = "1234"
    collection_url = "https://1234"
    description = "test"

    s: models.data.Data = models.data.Data(
        name="1",
        url="1",
        collection_uuid=collection_uuid,
        collection_url=collection_url,
        description=description,
    )
    t: models.tag.Tag = models.tag.Tag(name="test", data=[s])

    assert t.id == 1 and t.name == "test" and t.data == [s]
    t2: models.tag.Tag = models.tag.Tag(name="test2", data=[s])
    assert t2.id == 2

    s: models.data.Data = models.data.Data(
        name="source_with_tags",
        url="1",
        tags=[t, t2],
        collection_uuid=collection_uuid,
        collection_url=collection_url,
        description=description,
    )
    assert s.tags == [t, t2]


def test_json(app):
    t: models.tag.Tag = models.tag.Tag.query.filter_by(name="test").first()
    t_json = t.toJSON()

    assert list(t_json.keys()) == ["id", "name"]
    assert t_json["id"] == t.id and t_json["name"] == t.name


def test_str_repr(app):
    t: models.tag.Tag = models.tag.Tag.query.filter_by(name="test").first()
    t_str = str(t)

    assert t_str == f"<Tag(id={t.id}, name='{t.name}')>"
