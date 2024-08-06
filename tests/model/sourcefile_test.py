from uuid import uuid4

import aero.models as models


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


def test_json(app):
    f: models.source_file.SourceFile = models.source_file.SourceFile.query.filter_by(
        file_name="test"
    ).first()
    f_json = f.toJSON()

    assert list(f_json.keys()) == [
        "file_name",
        "collection_url",
        "file_type",
        "file_size",
        "encoding",
    ]

    assert (
        f_json["file_name"] == "test"
        and f_json["collection_url"] == f.source_version.source.collection_url
        and f_json["file_type"] == "json"
        and f_json["file_size"] == 1
        and f_json["encoding"] == "utf-8"
    )


def test_str_repr(app):
    f: models.source_file.SourceFile = models.source_file.SourceFile.query.filter_by(
        file_name="test"
    ).first()
    f_str = str(f)

    assert (
        f_str
        == f"<SourceFile(id={f.id}, file_name={f.file_name}, file_size={f.size}, encoding={f.encoding})>"
    )


def test_set_defaults(app):
    f: models.source_file.SourceFile = models.source_file.SourceFile.query.filter_by(
        file_name="test"
    ).first()
    kwargs = f._set_defaults(**{})

    assert kwargs["encoding"] == "utf-8"

    kwargs = f._set_defaults(**{"encoding": "test"})
    assert kwargs["encoding"] == "test"
