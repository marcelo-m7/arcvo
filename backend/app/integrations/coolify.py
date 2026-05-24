from typing import Any

import httpx


class CoolifyClient:
    def __init__(self, host: str, api_key: str, webhook_url: str) -> None:
        self.host = host.rstrip("/")
        self.api_key = api_key
        self.webhook_url = webhook_url

    async def health(self) -> dict[str, Any]:
        if not self.host:
            return {"configured": False, "healthy": False, "status_code": None}
        async with httpx.AsyncClient(timeout=20, verify=False) as client:
            response = await client.get(f"{self.host}/api/v1/health")
        return {
            "configured": True,
            "healthy": response.status_code == 200,
            "status_code": response.status_code,
            "body": response.text[:120],
        }

    async def api_probe(self) -> dict[str, Any]:
        if not self.host or not self.api_key:
            return {
                "configured": False,
                "status_code": None,
                "detail": "Missing Coolify host or API key",
            }
        headers = {"Authorization": f"Bearer {self.api_key}", "Accept": "application/json"}
        async with httpx.AsyncClient(timeout=20, verify=False) as client:
            response = await client.get(f"{self.host}/api/v1/projects", headers=headers)
        detail = "ok"
        if response.status_code == 403:
            detail = "Coolify API key authenticated but lacks permission for project reads"
        elif response.status_code >= 400:
            detail = f"Coolify API returned HTTP {response.status_code}"
        return {"configured": True, "status_code": response.status_code, "detail": detail}

    async def trigger_deploy(self) -> dict[str, Any]:
        if not self.webhook_url:
            return {"configured": False, "triggered": False, "status_code": None}
        async with httpx.AsyncClient(timeout=30, verify=False) as client:
            response = await client.get(self.webhook_url)
        return {
            "configured": True,
            "triggered": 200 <= response.status_code < 300,
            "status_code": response.status_code,
            "body": response.text[:500],
        }
