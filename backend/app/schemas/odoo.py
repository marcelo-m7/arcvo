from pydantic import BaseModel


class OdooHealth(BaseModel):
    status: str
    configured: bool
    database: str | None = None
    server_version: str | None = None
    authenticated: bool = False
    uid: int | None = None
    tls_workaround_enabled: bool = False
