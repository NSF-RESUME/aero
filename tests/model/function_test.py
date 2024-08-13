from uuid import uuid4
import aero.models as models

F_UUID = uuid4()


def test_create(app):
    f: models.function.Function = models.function.Function(uuid=F_UUID)

    assert f.id == F_UUID and f.provenances == []


def test_json(app):
    f: models.function.Function = models.function.Function.query.filter_by(
        id=F_UUID
    ).first()
    f_json = f.toJSON()

    assert list(f_json.keys()) == ["id"]
    assert f_json["id"] == f.id


def test_str_repr(app):
    f: models.function.Function = models.function.Function.query.filter_by(
        id=F_UUID
    ).first()
    f_str = str(f)

    assert f_str == f"<Function(id={f.id})>"
