import datetime

import aero.models
import aero.models.data_version


def test_create_version(session, data):
    version = 1
    checksum = "chksm"
    v = aero.models.data_version.create_dataversion(
        session=session, version=version, checksum=checksum, data_id=data.id
    )

    assert isinstance(v.created_at, datetime.datetime)
    assert v.data == data
    assert v.provenance_contribution is None
    assert v.provenance_source is None
    assert v.data_file is None
