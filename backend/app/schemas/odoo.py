from typing import Any

from pydantic import BaseModel, Field


class OdooHealth(BaseModel):
    status: str
    integration_mode: str
    url: str
    database: str
    server_version: str | None = None
    authenticated: bool = False
    uid: int | None = None
    partner_count: int | None = None
    mcp_mode: str | None = None
    tls_workaround_enabled: bool = False


class OdooRecordList(BaseModel):
    model: str
    limit: int
    offset: int
    count: int
    records: list[dict[str, Any]]


class OdooRecordCreate(BaseModel):
    values: dict[str, Any] = Field(default_factory=dict)


class OdooRecordUpdate(BaseModel):
    values: dict[str, Any] = Field(default_factory=dict)
