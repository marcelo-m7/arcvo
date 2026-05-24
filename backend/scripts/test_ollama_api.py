import asyncio

import httpx


async def test() -> None:
    async with httpx.AsyncClient(verify=False, timeout=90) as c:
        r = await c.get("https://api.ollama.monynha.me/api/tags")
        models = [m["name"] for m in r.json()["models"]]
        print("Available models:", models)

        model = "qwen2.5:1.5b" if "qwen2.5:1.5b" in models else models[0]
        print(f"Testing generate with: {model}")

        prompt = (
            "Voce e um agente Arcvo. Responda somente JSON valido. "
            'Retorne: {"summary": "ok", "status": "completed", "progress": 100, "command": ""}'
        )
        r2 = await c.post(
            "https://api.ollama.monynha.me/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
        )
        print("generate status:", r2.status_code)
        if r2.status_code == 200:
            print("response:", r2.json().get("response", "")[:300])
        else:
            print("error:", r2.text[:200])


asyncio.run(test())
