import datetime

from uuid import uuid4

import aero.models as models


def test_create_source_version(app):
    with app.app_context():
        s: models.data.Data = models.data.Data(
            name="1",
            url="1",
            email="1",
            collection_uuid="1234",
            collection_url="https://1234",
            description="test",
        )

        checksum = str(uuid4())
        v: models.data_version.DataVersion = models.data_version.DataVersion(
            version=(s.last_version() + 1), data_id=s.id, checksum=checksum
        )

        assert (
            v.checksum == checksum
            and isinstance(v.created_at, datetime.date)
            and v.data_id == s.id
            and v.data == s
            and v.data_file is None
        )


def test_version_json(app):
    with app.app_context():
        s: models.data.Data = models.data.Data.query.filter_by(name="test").first()
        checksum = str(uuid4())
        v: models.data_version.DataVersion = models.data_version.DataVersion(
            version=(s.last_version().version + 1), data_id=s.id, checksum=checksum
        )
        v_dict = v.toJSON()

        keys = ["id", "data", "version", "created_at", "checksum", "data_file"]

        assert list(v_dict.keys()) == keys

        assert (
            v_dict["data"] == s.toJSON()
            and v_dict["version"] == s.last_version().version
            and v_dict["checksum"] == checksum
            and v_dict["data_file"] is None
        )


def test_version_repr(app):
    with app.app_context():
        s: models.data.Data = models.data.Data.query.filter_by(name="test").first()
        checksum = str(uuid4())
        v: models.data_version.DataVersion = models.data_version.DataVersion(
            version=(s.last_version().version + 1), data_id=s.id, checksum=checksum
        )
        v_str = str(v)

        assert (
            v_str
            == f"<DataVersion(id={v.id}, version={s.last_version().version}, data_id={s.id}, checksum={checksum}, data_file=None)>"
        )


def test_set_version_defaults(app):
    with app.app_context():
        s: models.data.Data = models.data.Data.query.filter_by(name="test").first()
        checksum = str(uuid4())
        v: models.data_version.DataVersion = models.data_version.DataVersion(
            version=(s.last_version().version + 1), data_id=s.id, checksum=checksum
        )

        kwargs = v._set_defaults(**{})

        assert "created_at" in kwargs.keys() and isinstance(
            kwargs["created_at"], datetime.date
        )

        time_now = datetime.datetime.now()
        kwargs = v._set_defaults(**{"created_at": time_now})

        assert kwargs["created_at"] == time_now
