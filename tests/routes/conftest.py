import pytest

from unittest import mock


@pytest.fixture(scope="session", autouse=True)
def _mock_auth():
    with mock.patch(
        "osprey.server.app.decorators.is_token_valid", return_value=True
    ) as _:
        yield
