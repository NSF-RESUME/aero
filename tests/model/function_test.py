import aero.models as models


def test_create(app):
    uuid = "1"
    f: models.function.Function = models.function.Function(uuid=uuid)

    assert f.id == 1 and f.uuid == uuid and f.provenances == []


def test_json(app):
    f: models.function.Function = models.function.Function.query.filter_by(id=1).first()
    f_json = f.toJSON()

    assert list(f_json.keys()) == ["id", "uuid"]
    assert f_json["id"] == f.id and f_json["uuid"] == f.uuid


def test_str_repr(app):
    f: models.function.Function = models.function.Function.query.filter_by(id=1).first()
    f_str = str(f)

    assert f_str == f"<Function(id={f.id}, uuid='{f.uuid}')>"
