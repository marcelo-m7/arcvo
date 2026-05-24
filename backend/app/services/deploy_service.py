import subprocess
from datetime import UTC, datetime
from pathlib import Path

from app.core.config import settings
from app.integrations.coolify import CoolifyClient
from app.integrations.odoo.client import OdooClient, OdooCredentials
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

        support = self._support_status()

        return ProductionStatus(
            branch=branch,
            commit=commit,
            dirty=dirty,
            coolify_health=coolify_health,
            coolify_api=coolify_api,
            ollama_ok=ollama_ok,
            ollama_health=ollama_health,
            support=support,
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

    @staticmethod
    def _support_status() -> dict[str, object]:
        credentials = OdooCredentials(
            url=settings.odoo_url,
            database=settings.odoo_db,
            username=settings.odoo_user,
            api_key=settings.odoo_api_key,
            allow_self_signed_ssl=settings.odoo_allow_self_signed_ssl,
        )
        client = OdooClient(credentials)
        now = datetime.now(UTC).replace(tzinfo=None).strftime("%Y-%m-%d %H:%M:%S")
        try:
            client.authenticate()
            helpdesk_total = client.search_count("arcvo.helpdesk.ticket")
            helpdesk_open = client.search_count(
                "arcvo.helpdesk.ticket",
                [["state", "not in", ["resolved", "closed"]]],
            )
            helpdesk_sla_breached = client.search_count(
                "arcvo.helpdesk.ticket",
                [
                    ["sla_deadline", "!=", False],
                    ["sla_deadline", "<", now],
                    ["state", "not in", ["resolved", "closed"]],
                ],
            )
            knowledge_total = client.search_count("arcvo.knowledge.article")
            knowledge_published = client.search_count(
                "arcvo.knowledge.article",
                [["state", "=", "published"]],
            )
            return {
                "available": True,
                "helpdesk_total": helpdesk_total,
                "helpdesk_open": helpdesk_open,
                "helpdesk_sla_breached": helpdesk_sla_breached,
                "knowledge_total": knowledge_total,
                "knowledge_published": knowledge_published,
                "error": None,
            }
        except Exception as exc:
            return {
                "available": False,
                "helpdesk_total": None,
                "helpdesk_open": None,
                "helpdesk_sla_breached": None,
                "knowledge_total": None,
                "knowledge_published": None,
                "error": str(exc),
            }


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
            password=settings.ollama_ui_senha,
        ),
    )
