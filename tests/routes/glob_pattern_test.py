"""Glob patterns as source-url matching rules.

Canonical semantics: ``*`` within one path segment, ``**`` across segments,
``?`` one character. Python 3.11 has no stdlib equivalent, so the translator is
hand-rolled and worth testing directly.
"""

from uuid import UUID
from uuid import uuid4

import pytest

from sqlmodel import select

import aero.models.data

from aero.models.data import Data
from aero.routers.data import _concrete_object_url
from aero.routers.data import _is_pattern
from aero.routers.data import _pattern_regex
from aero.routers.data import _pattern_specificity


TYPES = "/data/types"
SOURCE = "/data/source"
NOTIFY = "/data/notify"

HOST = "http://127.0.0.1:9000"
PATTERN = f"{HOST}/test-bucket/**/*.csv"


# --------------------------------------------------------------------------
# the translator
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "pattern, key, expected",
    [
        # ** spans any number of segments, including zero
        ("**/test-data/**", "test-bucket/test-data/a.csv", True),
        ("**/test-data/**", "a/b/test-data/c/d.csv", True),
        ("**/test-data/**", "test-bucket/other/a.csv", False),
        ("test-bucket/**/*.csv", "test-bucket/a/b/c.csv", True),
        ("test-bucket/**/*.csv", "test-bucket/c.csv", True),
        ("test-bucket/**/*.csv", "test-bucket/a/b/c.xml", False),
        ("test-bucket/**/*.csv", "other-bucket/a.csv", False),
        # a single * stays inside one segment -- the whole point of ** existing
        ("test-bucket/*/*.csv", "test-bucket/a/b.csv", True),
        ("test-bucket/*/*.csv", "test-bucket/a/b/c.csv", False),
        # ? is exactly one character
        ("logs/report-?.csv", "logs/report-1.csv", True),
        ("logs/report-?.csv", "logs/report-12.csv", False),
        # character classes
        ("logs/report-[0-9].csv", "logs/report-7.csv", True),
        ("logs/report-[0-9].csv", "logs/report-x.csv", False),
        # anchored at both ends
        ("bucket/a.csv", "bucket/a.csv.bak", False),
        ("bucket/a.csv", "other/bucket/a.csv", False),
        # regex metacharacters in a literal are escaped, not interpreted
        ("bucket/a.csv", "bucket/aXcsv", False),
    ],
)
def test_pattern_matching(pattern, key, expected):
    assert bool(_pattern_regex(pattern).match(key)) is expected


@pytest.mark.parametrize(
    "key, expected",
    [
        ("test-bucket/a.csv", False),
        ("test-bucket/**/*.csv", True),
        ("logs/report-?.csv", True),
        ("logs/report-[0-9].csv", True),
    ],
)
def test_is_pattern(key, expected):
    assert _is_pattern(key) is expected


def test_specificity_prefers_the_longest_literal_prefix():
    matching = ["**/*.csv", "test-bucket/**", "test-bucket/logs/**"]
    assert max(matching, key=_pattern_specificity) == "test-bucket/logs/**"


def test_a_question_mark_survives_registration(client):
    """`?` in a pattern is a glob, not the start of a query string.

    Normalizing a registered url with urlparse truncates `bucket/report-?.csv` to
    `bucket/report-`, which then matches nothing. Presigned notify urls still need
    their query stripped, so the two normalizers are deliberately separate.
    """
    _pattern_type(client, name="reports", url=f"{HOST}/logs/report-?.csv")

    listed = client.get(f"{TYPES}/reports").json()
    assert listed["urls"][0]["object_key"] == "logs/report-?.csv"

    resp = client.post(
        NOTIFY, json={"file_id": "logs/report-7.csv", "etag": "aaa", "size": 1}
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["source_key"] == "logs/report-7.csv"


def test_concrete_object_url_rebuilds_from_the_pattern_host():
    assert (
        _concrete_object_url(PATTERN, "test-bucket/a/b.csv")
        == f"{HOST}/test-bucket/a/b.csv"
    )
    # no scheme to contribute -> the key stands alone
    assert _concrete_object_url("test-bucket/**", "test-bucket/a.csv") == (
        "test-bucket/a.csv"
    )


# --------------------------------------------------------------------------
# resolution
# --------------------------------------------------------------------------


def _pattern_type(client, name="traffic", url=PATTERN):
    resp = client.post(
        SOURCE, json={"name": name, "url": url, "type": name, "no_copy": True}
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_an_unregistered_object_matching_a_pattern_resolves(client, session):
    body = _pattern_type(client)

    resp = client.post(
        NOTIFY,
        json={"file_id": "test-bucket/never/registered.csv", "etag": "aaa", "size": 1},
    )

    assert resp.status_code == 200, resp.text
    out = resp.json()
    assert out["status"] == "version created"
    assert out["data_id"] == body["id"]
    # the concrete key, not the pattern
    assert out["source_key"] == "test-bucket/never/registered.csv"


def test_version_records_the_concrete_key(client, session):
    body = _pattern_type(client)
    client.post(NOTIFY, json={"file_id": "test-bucket/a.csv", "etag": "aaa", "size": 1})

    d = session.exec(select(Data).where(Data.id == UUID(body["id"]))).first()
    assert d.last_version().source_key == "test-bucket/a.csv"
    assert d.last_version().data_file.file_name == "test-bucket/a.csv"


def test_dedup_stays_per_object_under_one_pattern(client, session):
    """Two objects matching the same pattern must not share a dedup bucket.

    If the pattern were recorded as source_key, b would be compared against a and
    a re-notify of a would compare against b — collapsing distinct objects into
    one change history.
    """
    body = _pattern_type(client)

    client.post(NOTIFY, json={"file_id": "test-bucket/a.csv", "etag": "aaa", "size": 1})
    client.post(NOTIFY, json={"file_id": "test-bucket/b.csv", "etag": "bbb", "size": 2})
    again = client.post(
        NOTIFY, json={"file_id": "test-bucket/a.csv", "etag": "aaa", "size": 1}
    )

    assert again.json()["status"] == "unchanged"
    d = session.exec(select(Data).where(Data.id == UUID(body["id"]))).first()
    assert sorted(v.source_key for v in d.versions) == [
        "test-bucket/a.csv",
        "test-bucket/b.csv",
    ]


def test_a_non_matching_object_still_404s(client):
    _pattern_type(client)

    resp = client.post(
        NOTIFY, json={"file_id": "other-bucket/a.csv", "etag": "aaa", "size": 1}
    )
    assert resp.status_code == 404, resp.text


def test_exact_registration_beats_a_pattern(client):
    """A specific object can be routed away from the type that globs it."""
    broad = _pattern_type(client, name="broad", url=PATTERN)
    exact = client.post(
        SOURCE,
        json={
            "name": "special",
            "url": f"{HOST}/test-bucket/special.csv",
            "type": "special",
            "no_copy": True,
        },
    ).json()

    resp = client.post(
        NOTIFY, json={"file_id": "test-bucket/special.csv", "etag": "aaa", "size": 1}
    )

    assert resp.json()["data_id"] == exact["id"]
    assert resp.json()["data_id"] != broad["id"]


def test_the_more_specific_pattern_wins(client):
    broad = _pattern_type(client, name="broad", url=f"{HOST}/**/*.csv")
    narrow = _pattern_type(client, name="narrow", url=f"{HOST}/test-bucket/logs/**")

    resp = client.post(
        NOTIFY, json={"file_id": "test-bucket/logs/a.csv", "etag": "aaa", "size": 1}
    )

    assert resp.json()["data_id"] == narrow["id"]
    assert resp.json()["data_id"] != broad["id"]


def test_equally_specific_patterns_are_a_conflict(client):
    """Same literal prefix and same length -- ranking cannot separate them.

    Falling through to alphabetical order would pick a winner silently; the
    ambiguity is the user's to resolve.
    """
    _pattern_type(client, name="one", url=f"{HOST}/test-bucket/*/a?.csv")
    _pattern_type(client, name="two", url=f"{HOST}/test-bucket/*/?1.csv")

    resp = client.post(
        NOTIFY, json={"file_id": "test-bucket/x/a1.csv", "etag": "aaa", "size": 1}
    )

    assert resp.status_code == 409, resp.text


def test_trigger_url_is_the_concrete_object(client, session):
    body = _pattern_type(client)
    client.post(
        NOTIFY, json={"file_id": "test-bucket/deep/a.csv", "etag": "aaa", "size": 1}
    )

    resp = client.get(f"/data/{body['id']}/latest")

    assert resp.status_code == 200, resp.text
    out = resp.json()
    assert out["source_key"] == "test-bucket/deep/a.csv"
    # carries the pattern's host, and is fetchable -- never the pattern itself
    assert out["trigger_url"] == f"{HOST}/test-bucket/deep/a.csv"
    assert "*" not in out["trigger_url"]


def test_latest_returns_no_url_rather_than_a_pattern(client, session):
    """A version with no matching entry must not fall back to a pattern Data.url."""
    body = _pattern_type(client)
    d = session.exec(select(Data).where(Data.id == UUID(body["id"]))).first()
    d.add_new_version(
        session=session, new_file="x", format="csv", checksum="zzz", size=1
    )

    out = client.get(f"/data/{body['id']}/latest").json()

    assert out["trigger_url"] is None


def test_notify_by_id_accepts_a_pattern_match(client):
    body = _pattern_type(client)

    ok = client.post(
        f"/data/{body['id']}/notify",
        json={"key": "test-bucket/anything.csv", "etag": "aaa", "size": 1},
    )
    assert ok.status_code == 200, ok.text
    assert ok.json()["source_key"] == "test-bucket/anything.csv"

    bad = client.post(
        f"/data/{body['id']}/notify",
        json={"key": "other-bucket/a.csv", "etag": "aaa", "size": 1},
    )
    assert bad.status_code == 404, bad.text


def test_a_pattern_needs_a_type(client):
    resp = client.post(
        SOURCE, json={"name": "loose", "url": PATTERN, "no_copy": True}
    )

    assert resp.status_code == 400, resp.text
    assert "pattern" in resp.json()["detail"]


def test_untyped_exact_sources_are_unaffected(client, session, monkeypatch):
    """The legacy Data.url scan still resolves a source with no type."""
    import aero.routers.data as data_router

    calls = []
    monkeypatch.setattr(
        data_router,
        "_run_event_ingestion",
        lambda session, data, **kw: calls.append(data) or {"status": "ok"},
    )
    _pattern_type(client)
    d = aero.models.data.create_data(
        session=session,
        name="legacy",
        url=f"{HOST}/old-bucket/legacy.csv",
        collection_url="https://globus.org/test",
        collection_uuid=uuid4(),
        description="",
    )

    resp = client.post(NOTIFY, json={"file_id": "old-bucket/legacy.csv"})

    assert resp.status_code == 200, resp.text
    assert calls[0].id == d.id
