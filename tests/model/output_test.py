import osprey.server.models as models


def test_create(app):
    name = "test"
    url = "test"

    o: models.output.Output = models.output.Output(name=name, url=url)

    # without output_version
    assert (
        o.id == 1
        and o.name == name
        and o.url == url
        and o.provenance_id is None
        and o.output_versions == []
    )

    filename = "test"
    version = 1
    checksum = "1"
    ov: models.output.OutputVersion = models.output.OutputVersion(
        filename=filename, version=version, checksum=checksum, output_id=o.id
    )

    assert o.output_versions == [ov]


def test_json(app):
    o: models.output.Output = models.output.Output.query.filter_by(id=1).first()
    o_json = o.toJSON()

    assert list(o_json.keys()) == ["id", "name", "url", "provenance_id", "versions"]

    assert (
        o_json["id"] == o.id
        and o_json["name"] == o.name
        and o_json["url"] == o.url
        and o_json["provenance_id"] == o.provenance_id
        and o_json["versions"] == [v.toJSON() for v in o.output_versions]
    )


def test_str_repr(app):
    o: models.output.Output = models.output.Output.query.filter_by(id=1).first()
    o_str = str(o)

    assert (
        o_str
        == f"<Output(id={o.id}, name='{o.name}', url='{o.url}', provenance_id={o.provenance_id}, versions={o.output_versions})>"
    )


def test_add_output_version(app):
    fn = "test1"
    checksum = "1"
    o: models.output.Output = models.output.Output(name="test1", url="test1")
    o.add_new_version(filename=fn, checksum="1")

    ov: models.output_version.OutputVersion = o.output_versions[-1]

    assert (
        len(o.output_versions) == 1
        and ov.filename == fn
        and ov.checksum == checksum
        and ov.output == o
        and ov.output_id == o.id
    )

    # add a second version by changing the checksum
    checksum2 = "2"
    o.add_new_version(filename=fn, checksum=checksum2)
    ov = o.output_versions
    assert len(ov) == 2 and ov[-1].checksum == checksum2

    # check that a new version isn't added when checksum doesn't change
    o.add_new_version(filename=fn, checksum=checksum2)
    assert len(o.output_versions) == 2
