import ssl
import xmlrpc.client
from dataclasses import dataclass
from typing import Any

import httpx


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

    def search_read(
        self,
        model: str,
        domain: list[Any] | None = None,
        fields: list[str] | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        kwargs: dict[str, Any] = {"limit": limit, "offset": offset}
        if fields:
            kwargs["fields"] = fields
        return self.execute_kw(model, "search_read", [domain or []], kwargs)

    def search(
        self,
        model: str,
        domain: list[Any] | None = None,
        limit: int | None = None,
    ) -> list[int]:
        kwargs: dict[str, Any] = {}
        if limit is not None:
            kwargs["limit"] = limit
        return self.execute_kw(model, "search", [domain or []], kwargs)

    def search_count(self, model: str, domain: list[Any] | None = None) -> int:
        return int(self.execute_kw(model, "search_count", [domain or []], {}))

    def create(self, model: str, values: dict[str, Any]) -> int:
        return int(self.execute_kw(model, "create", [values], {}))

    def write(self, model: str, record_id: int, values: dict[str, Any]) -> bool:
        return bool(self.execute_kw(model, "write", [[record_id], values], {}))

    def execute_kw(
        self,
        model: str,
        method: str,
        args: list[Any],
        kwargs: dict[str, Any] | None = None,
    ) -> Any:
        uid = self._uid or self.authenticate()
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
            raise OdooClientError(f"Odoo RPC call failed for {model}.{method}: {exc}") from exc

    async def jsonrpc_version(self) -> dict[str, Any]:
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {"service": "common", "method": "version", "args": []},
            "id": 1,
        }
        verify = not self.credentials.allow_self_signed_ssl
        async with httpx.AsyncClient(verify=verify, timeout=20) as client:
            response = await client.post(f"{self.credentials.url}/jsonrpc", json=payload)
            response.raise_for_status()
            data = response.json()
            if "error" in data:
                raise OdooClientError(str(data["error"]))
            return data["result"]

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
