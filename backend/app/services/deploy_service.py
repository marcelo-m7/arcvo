import subprocess
from pathlib import Path

from app.core.config import settings
from app.integrations.coolify import CoolifyClient
from app.integrations.ollama import OllamaClient
from app.schemas.deploy import CoolifyDeployResult, ProductionStatus

ROOT_DIR = Path(__file__).resolve().parents[3]


class DeployService:
    def __init__(self, coolify: CoolifyClient, ollama: OllamaClient) -> None:
        self.coolify = coolify
        self.ollama = ollama

    async def status(self) -> ProductionStatus:
        branch = self._git(["branch", "--show-current"])
        commit = self._git(["rev-parse", "--short", "HEAD"])
        dirty = bool(self._git(["status", "--porcelain"]))
        coolify_health = await self.coolify.health()
        coolify_api = await self.coolify.api_probe()
        try:
            ollama_health = await self.ollama.health()
            ollama_ok = True
        except Exception as exc:
            ollama_health = {"error": str(exc)}
            ollama_ok = False
        return ProductionStatus(
            branch=branch,
            commit=commit,
            dirty=dirty,
            coolify_health=coolify_health,
            coolify_api=coolify_api,
            ollama_ok=ollama_ok,
            ollama_health=ollama_health,
        )

    async def trigger_coolify(self) -> CoolifyDeployResult:
        result = await self.coolify.trigger_deploy()
        return CoolifyDeployResult(**result)

    @staticmethod
    def _git(args: list[str]) -> str:
        completed = subprocess.run(
            ["git", *args],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
        return completed.stdout.strip()


def get_deploy_service() -> DeployService:
    return DeployService(
        coolify=CoolifyClient(
            host=settings.coolify_host,
            api_key=settings.coolify_api_key,
            webhook_url=settings.coolify_arcvo_webhook,
        ),
        ollama=OllamaClient(
            base_url=settings.ollama_url,
            model=settings.ollama_model,
            timeout=settings.ollama_timeout_seconds,
        ),
    )
