from typing import Any

import httpx


class OllamaError(RuntimeError):
    """Raised when Ollama cannot satisfy a request."""


class OllamaClient:
    def __init__(
        self, base_url: str, model: str, timeout: float = 60.0, password: str = ""
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self._password = password

    def _headers(self) -> dict[str, str]:
        if self._password:
            return {"Authorization": f"Bearer {self._password}"}
        return {}

    async def health(self) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=10, verify=False) as client:
            for path in ("/api/version", "/ollama/api/version"):
                response = await client.get(
                    f"{self.base_url}{path}", headers=self._headers()
                )
                if response.status_code != 404:
                    break
            response.raise_for_status()
            return response.json()

    async def generate(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.2},
        }
        async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
            for path in ("/api/generate", "/ollama/api/generate"):
                response = await client.post(
                    f"{self.base_url}{path}",
                    json=payload,
                    headers=self._headers(),
                )
                if response.status_code != 404:
                    break
            if response.status_code >= 400:
                raise OllamaError(f"Ollama generation failed with HTTP {response.status_code}")
            data = response.json()
        text = data.get("response")
        if not isinstance(text, str):
            raise OllamaError("Ollama response did not include text")
        return text.strip()
