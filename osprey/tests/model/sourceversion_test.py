import datetime

from uuid import uuid4

from osprey.tests.conftest import Source
from osprey.tests.conftest import SourceVersion


def test_create_source_version(app):
    with app.app_context():
        s: Source = Source(name="1", url="1", email="1")

        checksum = str(uuid4())
        v: SourceVersion = SourceVersion(
            version=(s.last_version() + 1), source_id=s.id, checksum=checksum
        )

        assert (
            v.version == 1
            and v.checksum == checksum
            and isinstance(v.created_at, datetime.date)
            and v.source_id == s.id
            and v.source == s
            and v.source_file is None
        )


def test_version_json(app):
    with app.app_context():
        s: Source = Source.query.filter_by(name="test").first()
        checksum = str(uuid4())
        v: SourceVersion = SourceVersion(
            version=(s.last_version().version + 1), source_id=s.id, checksum=checksum
        )
        v_dict = v.toJSON()

        keys = ["id", "source", "version", "created_at", "checksum", "source_file"]

        assert list(v_dict.keys()) == keys

        assert (
            v_dict["source"] == s.toJSON()
            and v_dict["version"] == s.last_version().version
            and v_dict["checksum"] == checksum
            and v_dict["source_file"] is None
        )


def test_version_repr(app):
    with app.app_context():
        s: Source = Source.query.filter_by(name="test").first()
        checksum = str(uuid4())
        v: SourceVersion = SourceVersion(
            version=(s.last_version().version + 1), source_id=s.id, checksum=checksum
        )
        v_str = str(v)

        assert (
            v_str
            == f"<SourceVersion(id={v.id}, version={s.last_version().version}, source_id={s.id}, checksum={checksum}, source_file=None)>"
        )


def test_set_version_defaults(app):
    with app.app_context():
        s: Source = Source.query.filter_by(name="test").first()
        checksum = str(uuid4())
        v: SourceVersion = SourceVersion(
            version=(s.last_version().version + 1), source_id=s.id, checksum=checksum
        )

        kwargs = v._set_defaults(**{})

        assert "created_at" in kwargs.keys() and isinstance(
            kwargs["created_at"], datetime.date
        )

        time_now = datetime.datetime.now()
        kwargs = v._set_defaults(**{"created_at": time_now})

        assert kwargs["created_at"] == time_now
