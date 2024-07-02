import osprey.server.models as models


def test_create(app):
    name = "test"
    url = "test"
    filename = "test"
    version = 1
    checksum = "1"

    o: models.output.Output = models.output.Output(name=name, url=url)
    ov: models.output_version.OutputVersion = models.output_version.OutputVersion(
        filename=filename, version=version, checksum=checksum, output_id=o.id
    )

    assert (
        ov.filename == filename
        and ov.version == version
        and ov.checksum == checksum
        and ov.output_id == o.id
        and ov.output == o
    )


def test_json(app):
    ov: models.output_version.OutputVersion = (
        models.output_version.OutputVersion.query.filter_by(id=1).first()
    )
    ov_json = ov.toJSON()

    assert list(ov_json.keys()) == ["id", "filename", "version", "checksum"]
    assert (
        ov_json["id"] == ov.id
        and ov_json["filename"] == ov.filename
        and ov_json["version"] == ov.version
        and ov_json["checksum"] == ov.checksum
    )


def test_str_repr(app):
    ov: models.output_version.OutputVersion = (
        models.output_version.OutputVersion.query.filter_by(id=1).first()
    )
    ov_str = str(ov)

    assert (
        ov_str
        == f"<OutputVersion(id={ov.id}, filename='{ov.filename}', version_id={ov.version}, checksum='{ov.checksum}')>"
    )
