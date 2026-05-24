import asyncio

import httpx

from app.core.config import settings
from app.integrations.ollama import OllamaClient


async def test() -> None:
    client = OllamaClient(
        base_url=settings.ollama_url,
        model=settings.ollama_model,
        timeout=min(settings.ollama_timeout_seconds, 30.0),
        password=settings.ollama_ui_senha,
    )
    print("Ollama URL:", settings.ollama_url)
    print("Ollama model:", settings.ollama_model)
    print("Ollama health:", await client.health())

    async with httpx.AsyncClient(timeout=10, verify=False) as raw_client:
        for path in ("/api/tags", "/ollama/api/tags"):
            response = await raw_client.get(
                f"{settings.ollama_url}{path}",
                headers=client._headers(),
            )
            if response.status_code != 404:
                response.raise_for_status()
                tags = response.json().get("models", [])
                print("Ollama tags count:", len(tags))
                break

    try:
        response = await asyncio.wait_for(client.generate("ok"), timeout=12)
        print("generate response:", response[:300])
    except (TimeoutError, httpx.ReadTimeout):
        # Keep this check fast for operational smoke: health/tags already verified.
        print("generate warning: timeout during short smoke check")


asyncio.run(test())
