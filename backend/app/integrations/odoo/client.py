import ssl
import time
import xmlrpc.client
from dataclasses import dataclass
from typing import Any

_RETRY_ERRORS = (ConnectionResetError, BrokenPipeError, TimeoutError)
_TRANSIENT_SUBSTRINGS = ("EOF occurred", "Connection refused", "timed out", "reset by peer")


def _is_transient(exc: Exception) -> bool:
    if isinstance(exc, _RETRY_ERRORS):
        return True
    msg = str(exc).lower()
    return any(s.lower() in msg for s in _TRANSIENT_SUBSTRINGS)


class OdooClientError(RuntimeError):
    """Raised when Odoo cannot be reached or returns an RPC error."""


@dataclass(frozen=True)
class OdooCredentials:
    url: str
    database: str
    username: str
    api_key: str
    allow_self_signed_ssl: bool = False


class OdooClient:
    def __init__(self, credentials: OdooCredentials) -> None:
        self.credentials = credentials
        self._uid: int | None = None

    @property
    def uid(self) -> int | None:
        return self._uid

    def version(self) -> dict[str, Any]:
        try:
            return self._common_proxy().version()
        except Exception as exc:
            raise OdooClientError(f"Failed to read Odoo version: {exc}") from exc

    def authenticate(self) -> int:
        try:
            uid = self._common_proxy().authenticate(
                self.credentials.database,
                self.credentials.username,
                self.credentials.api_key,
                {},
            )
        except Exception as exc:
            raise OdooClientError(f"Failed to authenticate with Odoo: {exc}") from exc

        if not uid:
            raise OdooClientError("Odoo authentication failed")

        self._uid = int(uid)
        return self._uid

    def execute_kw(
        self,
        model: str,
        method: str,
        args: list[Any],
        kwargs: dict[str, Any] | None = None,
        _retries: int = 2,
    ) -> Any:
        uid = self._uid or self.authenticate()
        last_exc: Exception | None = None
        for attempt in range(_retries + 1):
            try:
                return self._object_proxy().execute_kw(
                    self.credentials.database,
                    uid,
                    self.credentials.api_key,
                    model,
                    method,
                    args,
                    kwargs or {},
                )
            except Exception as exc:
                last_exc = exc
                if attempt < _retries and _is_transient(exc):
                    self._uid = None  # force re-auth on next attempt
                    time.sleep(0.5 * (attempt + 1))
                    continue
                break
        raise OdooClientError(
            f"Odoo RPC call failed for {model}.{method}: {last_exc}"
        ) from last_exc

    def _common_proxy(self) -> xmlrpc.client.ServerProxy:
        return self._proxy("/xmlrpc/2/common")

    def _object_proxy(self) -> xmlrpc.client.ServerProxy:
        return self._proxy("/xmlrpc/2/object")

    def _proxy(self, endpoint: str) -> xmlrpc.client.ServerProxy:
        context = None
        if self.credentials.allow_self_signed_ssl:
            context = ssl._create_unverified_context()
        return xmlrpc.client.ServerProxy(
            f"{self.credentials.url.rstrip('/')}{endpoint}",
            context=context,
            allow_none=True,
        )
