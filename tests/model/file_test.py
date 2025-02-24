from aero.models.data_file import create_datafile


def test_create_datafile(session, version):
    file_name = "file.name"
    size = 1
    f = create_datafile(
        session=session, file_name=file_name, size=size, version_id=version.id
    )

    assert f.version == version
    assert f.encoding == "utf-8"
    assert f.file_type is None
