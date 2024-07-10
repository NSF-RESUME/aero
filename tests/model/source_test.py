import datetime
import json
import pytest

from unittest import mock
from uuid import uuid4

import osprey.server.models as models
from osprey.server.app.utils import Config
from osprey.server.lib.globus_flow import FlowEnum
from osprey.server.lib.error import ServiceError


def test_create_source(app):
    with app.app_context():
        s: models.source.Source = models.source.Source(
            name="test", url="test", email="test"
        )
        assert (
            s.name == "test"
            and s.url == "test"
            and s.collection_uuid is None
            and s.collection_url is None
            and s.description is None
            and s.timer == 86400
            and s.verifier is None
            and s.modifier is None
            and s.email == "test"
            and s.user_endpoint is None
            and s.timer_job_id == "1111"
            and s.flow_kind == 0
            and s.versions == []
            and s.tags == []
        )


def test_json_repr(app):
    with app.app_context():
        s: models.source.Source = models.source.Source.query.filter_by(
            name="test"
        ).first()
        s_dict = s.toJSON()

        assert list(s_dict.keys()) == [
            "id",
            "name",
            "url",
            "collection_uuid",
            "collection_url",
            "user_endpoint",
            "description",
            "timer",
            "verifier",
            "modifier",
            "email",
            "available_versions",
        ], list(s_dict.keys())

        assert (
            s_dict["id"] == s.id
            and s_dict["name"] == s.name
            and s_dict["url"] == s.url
            and s_dict["collection_uuid"] == s.collection_uuid
            and s_dict["collection_url"] == s.collection_url
            and s_dict["description"] == s.description
            and s_dict["timer"] == s.timer
            and s_dict["verifier"] == s.verifier
            and s_dict["modifier"] == s.modifier
            and s_dict["email"] == s.email
            and s_dict["available_versions"] == 0
        )


def test_str_repr(app):
    with app.app_context():
        s: models.source.Source = models.source.Source.query.filter_by(
            name="test"
        ).first()
        s_str = str(s)
        assert (
            s_str
            == f"<Source(id={s.id}, name={s.name}, url={s.url}, collection_uuid={s.collection_uuid}, collection_url={s.collection_url}, description={s.description})>"
        ), s_str


def test_add_source_version(app):
    size = 1
    checksum = "1234"
    fformat = "csv"
    new_file = "test2"

    with app.app_context():
        s: models.source.Source = models.source.Source.query.filter_by(
            name="test"
        ).first()
        _ = s.add_new_version(
            new_file=new_file, format=fformat, checksum=checksum, size=size
        )

        v: models.source_version.SourceVersion = s.last_version()

        assert (
            v.checksum == "1234"
            and v.created_at is not None
            and v.source_id == s.id
            and v.source == s
            and v.source_file.file_name == new_file
            and v.source_file.file_type == fformat
            and v.source_file.size == size
            and v.source_file.encoding == "utf-8"
            and v.source_file.source_version_id == v.id
            and v.source_file.source_version == v
        )

        new_checksum = "12345"
        # test adding a version when a version already exists
        _ = s.add_new_version(
            new_file=new_file, format=fformat, checksum=new_checksum, size=size
        )
        assert len(s.versions) == 2 and s.versions[-1].checksum == new_checksum

        # test what happens if checksum doesn't change
        _ = s.add_new_version(
            new_file=new_file, format=fformat, checksum=new_checksum, size=size
        )

        assert len(s.versions) == 2


def test_policy_flow(app):
    with app.app_context():
        f: models.function.Function = models.function.Function(uuid="1")
        function_id = f.id
        function_args = json.dumps(
            {
                "endpoint": "123",
                "function": "456",
                "tasks": {"endpoint": "123", "function": "456"},
            }
        )
        contributed_to = []

        s: models.source.Source = models.source.Source.query.filter_by(
            name="test"
        ).first()
        derived_from = [s]

        # default policy
        p: models.provenance.Provenance = models.provenance.Provenance(
            function_id=function_id,
            function_args=function_args,
            derived_from=derived_from,
            contributed_to=contributed_to,
        )

        policy_id = s.rerun_flow()
        assert policy_id == [3]

        # p: Provenance = Provenance(function_id=function_id, derived_from=derived_from, contributed_to=contributed_to, policy=2)

        p.policy = 2
        policy_id = s.rerun_flow()
        assert policy_id == [2]

        # p: Provenance = Provenance(function_id=function_id, derived_from=derived_from, contributed_to=contributed_to, policy=1)
        p.policy = 1
        policy_id = s.rerun_flow()
        assert policy_id == [1]

        # p: Provenance = Provenance(function_id=function_id, derived_from=derived_from, contributed_to=contributed_to, policy=0)
        p.policy = 0
        policy_id = s.rerun_flow()
        assert policy_id == [0]


def test_last_version(app):
    with app.app_context():
        s: models.source.Source = models.source.Source(name="1", url="1", email="1")
        assert s.last_version() == 0

        s.add_new_version("1", "1", "2", 1)
        assert isinstance(s.last_version(), models.source_version.SourceVersion)


def test_timer_readable(app):
    with app.app_context():
        s: models.source.Source = models.source.Source.query.filter_by(
            name="test"
        ).first()
        assert isinstance(s.timer_readable(), str)  # probably should test str formats

        s: models.source.Source = models.source.Source(
            name="1", url="1", email="1", timer=0
        )
        assert s.timer_readable() is None


# TODO: delete as validation like this is not necessary
def test_source_validate(app):
    with app.app_context():
        with pytest.raises(ServiceError):
            _: models.source.Source = models.source.Source(name="1", email="1")


def test_set_defaults(app):
    with app.app_context():
        s: models.source.Source = models.source.Source(name="1", url="1", email="1")
        kwargs = s._set_defaults(**{})

        assert (
            kwargs["timer"] == 86400
            and kwargs["flow_kind"] == FlowEnum.NONE
            and kwargs["user_endpoint"] == Config.GLOBUS_WORKER_UUID
        )

        in_kwargs = {"timer": 2, "verifier": 1, "modifier": 1, "user_endpoint": "1"}
        kwargs = s._set_defaults(**in_kwargs)

        assert (
            kwargs["timer"] == in_kwargs["timer"]
            and kwargs["user_endpoint"] == in_kwargs["user_endpoint"]
            and kwargs["flow_kind"] == FlowEnum.VERIFY_AND_MODIFY
        )

        in_kwargs.pop("modifier")
        kwargs = s._set_defaults(**in_kwargs)

        assert kwargs["flow_kind"] == FlowEnum.VERIFY_OR_MODIFY

        in_kwargs["flow_kind"] = FlowEnum.USER_FLOW
        kwargs = s._set_defaults(**in_kwargs)

        assert kwargs["flow_kind"] == FlowEnum.USER_FLOW


def test_start_time_flow(app):
    with app.app_context():
        s: models.source.Source = models.source.Source(name="1", url="1", email="1")

        with pytest.raises(ServiceError):
            s._start_timer_flow()


def test_get_timer_job(app):
    with app.app_context():
        s: models.source.Source = models.source.Source(name="1", url="1", email="1")
        with mock.patch("osprey.server.lib.globus_flow.create_client") as _:
            _ = s.get_timer_job()


def test_last_refreshed_at(app):
    with app.app_context():
        s: models.source.Source = models.source.Source(name="1", url="1", email="1")

        with mock.patch("osprey.server.lib.globus_flow.create_client") as _:
            s.last_refreshed_at()

        with (
            mock.patch(
                "osprey.server.models.source.Source.get_timer_job", return_value=None
            ) as _,
            mock.patch("osprey.server.lib.globus_flow.create_client") as _,
        ):
            s.last_refreshed_at()


def test_create_source_version(app):
    with app.app_context():
        s: models.source.Source = models.source.Source(name="1", url="1", email="1")

        checksum = str(uuid4())
        v: models.source_version.SourceVersion = models.source_version.SourceVersion(
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
        s: models.source.Source = models.source.Source.query.filter_by(
            name="test"
        ).first()
        checksum = str(uuid4())
        v: models.source_version.SourceVersion = models.source_version.SourceVersion(
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
        s: models.source.Source = models.source.Source.query.filter_by(
            name="test"
        ).first()
        checksum = str(uuid4())
        v: models.source_version.SourceVersion = models.source_version.SourceVersion(
            version=(s.last_version().version + 1), source_id=s.id, checksum=checksum
        )
        v_str = str(v)

        assert (
            v_str
            == f"<SourceVersion(id={v.id}, version={s.last_version().version}, source_id={s.id}, checksum={checksum}, source_file=None)>"
        )


def test_set_version_defaults(app):
    with app.app_context():
        s: models.source.Source = models.source.Source.query.filter_by(
            name="test"
        ).first()
        checksum = str(uuid4())
        v: models.source_version.SourceVersion = models.source_version.SourceVersion(
            version=(s.last_version().version + 1), source_id=s.id, checksum=checksum
        )

        kwargs = v._set_defaults(**{})

        assert "created_at" in kwargs.keys() and isinstance(
            kwargs["created_at"], datetime.date
        )

        time_now = datetime.datetime.now()
        kwargs = v._set_defaults(**{"created_at": time_now})

        assert kwargs["created_at"] == time_now


def test_create_source_file(app):
    with app.app_context():
        file_name = "test"
        file_type = "json"
        size = 1
        encoding = "utf-8"

        s: models.source.Source = models.source.Source.query.filter_by(
            name="test"
        ).first()
        checksum = str(uuid4())
        v: models.source_version.SourceVersion = models.source_version.SourceVersion(
            version=(s.last_version().version + 1), source_id=s.id, checksum=checksum
        )

        f: models.source_file.SourceFile = models.source_file.SourceFile(
            file_name=file_name,
            file_type=file_type,
            size=size,
            encoding=encoding,
            source_version_id=v.id,
            source_version=v,
        )

        assert (
            f.file_name == file_name
            and f.file_type == file_type
            and f.size == size
            and f.encoding == encoding
            and f.source_version_id == v.id
            and f.source_version == v
        )
