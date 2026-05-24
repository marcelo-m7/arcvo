from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core.internal_access import require_internal_request


class DummyRequest:
    def __init__(self, host: str | None) -> None:
        self.client = SimpleNamespace(host=host) if host is not None else None


@pytest.mark.parametrize("host", ["127.0.0.1", "10.0.1.5", "192.168.0.20"])
def test_require_internal_request_allows_private_ranges(host: str) -> None:
    require_internal_request(DummyRequest(host))


def test_require_internal_request_blocks_public_ip() -> None:
    with pytest.raises(HTTPException):
        require_internal_request(DummyRequest("8.8.8.8"))
