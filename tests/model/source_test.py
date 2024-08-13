import datetime
import json
import pytest

from unittest import mock
from uuid import uuid4

import aero.models as models
from aero.globus.error import ServiceError


def test_create_source(app):
    collection_uuid = "1234"
    collection_url = "https://1234"
    description = "test"

    with app.app_context():
        s: models.data.Data = models.data.Data(
            name="test",
            url="test",
            email="test",
            collection_uuid=collection_uuid,
            collection_url=collection_url,
            description=description,
        )
        assert (
            s.name == "test"
            and s.url == "test"
            and s.collection_uuid == collection_uuid
            and s.collection_url == collection_url
            and s.description == description
            and s.timer == 86400
            and s.vm_func is None
            and s.email == "test"
            and s.user_endpoint is None
            and s.timer_job_id == "1111"
            and s.flow_kind == -1
            and s.versions == []
            and s.tags == []
        )


def test_json_repr(app):
    with app.app_context():
        s: models.data.Data = models.data.Data.query.filter_by(name="test").first()
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
            "vm_func",
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
            and s_dict["vm_func"] == s.vm_func
            and s_dict["email"] == s.email
            and s_dict["available_versions"] == 0
        )


def test_str_repr(app):
    with app.app_context():
        s: models.data.Data = models.data.Data.query.filter_by(name="test").first()
        s_str = str(s)
        assert (
            s_str
            == f"<Data(id={s.id}, name={s.name}, url={s.url}, collection_uuid={s.collection_uuid}, collection_url={s.collection_url}, description={s.description})>"
        ), s_str


def test_add_source_version(app):
    size = 1
    checksum = "1234"
    fformat = "csv"
    new_file = "test2"

    with app.app_context():
        s: models.data.Data = models.data.Data.query.filter_by(name="test").first()
        _ = s.add_new_version(
            new_file=new_file, format=fformat, checksum=checksum, size=size
        )

        v: models.data_version.DataVersion = s.last_version()

        assert (
            v.checksum == "1234"
            and v.created_at is not None
            and v.data_id == s.id
            and v.data == s
            and v.data_file.file_name == new_file
            and v.data_file.file_type == fformat
            and v.data_file.size == size
            and v.data_file.encoding == "utf-8"
            and v.data_file.version_id == v.id
            and v.data_file.version == v
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
        f: models.function.Function = models.function.Function(uuid=uuid4())
        function_id = f.id
        function_args = json.dumps(
            {
                "endpoint": "123",
                "function": "456",
                "tasks": {"endpoint": "123", "function": "456"},
            }
        )
        contributed_to = []

        s: models.data.Data = models.data.Data.query.filter_by(name="test").first()
        derived_from = [s]

        # default policy
        p: models.provenance.Provenance = models.provenance.Provenance(
            function_id=function_id,
            function_args=function_args,
            derived_from=derived_from,
            contributed_to=contributed_to,
        )

        policy_id = s.rerun_flow()
        assert policy_id == [models.provenance.PolicyEnum.NONE]

        # p: Provenance = Provenance(function_id=function_id, derived_from=derived_from, contributed_to=contributed_to, policy=2)

        p.policy = 3
        policy_id = s.rerun_flow()
        assert policy_id == [3]

        # p: Provenance = Provenance(function_id=function_id, derived_from=derived_from, contributed_to=contributed_to, policy=1)
        p.policy = 2
        policy_id = s.rerun_flow()
        assert policy_id == [2]

        # p: Provenance = Provenance(function_id=function_id, derived_from=derived_from, contributed_to=contributed_to, policy=0)
        p.policy = 1
        policy_id = s.rerun_flow()
        assert policy_id == [1]


def test_last_version(app):
    with app.app_context():
        s: models.data.Data = models.data.Data(
            name="1",
            url="1",
            email="1",
            collection_uuid="1234",
            collection_url="https://1234",
            description="test",
        )
        assert s.last_version() == 0

        s.add_new_version("1", "1", "2", 1)
        assert isinstance(s.last_version(), models.data_version.DataVersion)


def test_timer_readable(app):
    with app.app_context():
        s: models.data.Data = models.data.Data.query.filter_by(name="test").first()
        assert isinstance(s.timer_readable(), str)  # probably should test str formats

        s: models.data.Data = models.data.Data(
            name="1",
            url="1",
            email="1",
            timer=0,
            collection_uuid="1234",
            collection_url="https://1234",
            description="test",
        )
        assert s.timer_readable() is None


# TODO: delete as validation like this is not necessary
# def test_source_validate(app):
#     with app.app_context():
#         with pytest.raises(ServiceError):
#             _: models.data.Data = models.data.Data(name="1", email="1")


# def test_set_defaults(app):
#     with app.app_context():
#         s: models.data.Source = models.data.Source(name="1", url="1", email="1")
#         kwargs = s._set_defaults(**{})

#         assert (
#             kwargs["timer"] == 86400
#             and kwargs["flow_kind"] == FlowEnum.NONE
#             and kwargs["user_endpoint"] == Config.GLOBUS_WORKER_UUID
#         )

#         in_kwargs = {"timer": 2, "verifier": 1, "modifier": 1, "user_endpoint": "1"}
#         kwargs = s._set_defaults(**in_kwargs)

#         assert (
#             kwargs["timer"] == in_kwargs["timer"]
#             and kwargs["user_endpoint"] == in_kwargs["user_endpoint"]
#             and kwargs["flow_kind"] == FlowEnum.VERIFY_AND_MODIFY
#         )

#         in_kwargs.pop("modifier")
#         kwargs = s._set_defaults(**in_kwargs)

#         assert kwargs["flow_kind"] == FlowEnum.VERIFY_OR_MODIFY

#         in_kwargs["flow_kind"] = FlowEnum.USER_FLOW
#         kwargs = s._set_defaults(**in_kwargs)

#         assert kwargs["flow_kind"] == FlowEnum.USER_FLOW


def test_start_time_flow(app):
    with app.app_context():
        s: models.data.Data = models.data.Data(
            name="1",
            url="1",
            email="1",
            collection_uuid="1234",
            collection_url="https://1234",
            description="test",
        )

        with pytest.raises(ServiceError):
            s._start_timer_flow()


def test_get_timer_job(app):
    with app.app_context():
        s: models.data.Data = models.data.Data(
            name="1",
            url="1",
            email="1",
            collection_uuid="1234",
            collection_url="https://1234",
            description="test",
        )
        with mock.patch("aero.globus.flow.create_client") as _:
            _ = s.get_timer_job()


def test_last_refreshed_at(app):
    with app.app_context():
        s: models.data.Data = models.data.Data(
            name="1",
            url="1",
            email="1",
            collection_uuid="1234",
            collection_url="https://1234",
            description="test",
        )

        with mock.patch("aero.globus.flow.create_client") as _:
            s.last_refreshed_at()

        with (
            mock.patch("aero.models.data.Data.get_timer_job", return_value=None) as _,
            mock.patch("aero.globus.flow.create_client") as _,
        ):
            s.last_refreshed_at()


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
            v.version == 1
            and v.checksum == checksum
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


def test_create_source_file(app):
    with app.app_context():
        file_name = "test"
        file_type = "json"
        size = 1
        encoding = "utf-8"

        s: models.data.Data = models.data.Data.query.filter_by(name="test").first()
        checksum = str(uuid4())
        v: models.data_version.DataVersion = models.data_version.DataVersion(
            version=(s.last_version().version + 1), data_id=s.id, checksum=checksum
        )

        f: models.data_file.DataFile = models.data_file.DataFile(
            file_name=file_name,
            file_type=file_type,
            size=size,
            encoding=encoding,
            version_id=v.id,
            version=v,
        )

        assert (
            f.file_name == file_name
            and f.file_type == file_type
            and f.size == size
            and f.encoding == encoding
            and f.version_id == v.id
            and f.version == v
        )
