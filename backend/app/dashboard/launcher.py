from __future__ import annotations

import os

from app.core.config import settings
from app.dashboard.tools import ArcvoDashboardTools

SUPPORTED_HERMES_PROVIDERS = {"openai", "azure", "anthropic", "gemini", "google"}


def _build_dashboard_prompt() -> str:
    return (
        "You are Arcvo Operations Assistant. "
        "Prioritize concise, operational responses in Portuguese. "
        "Never invent Odoo records; use tools for reads/writes. "
        "When changing state, explain what was changed and why."
    )


def create_dashboard_agent():
    from hermes.core import Agent

    provider = settings.hermes_provider.strip().lower()
    if provider not in SUPPORTED_HERMES_PROVIDERS:
        if settings.gemini_api_key:
            provider = "gemini"
        else:
            raise RuntimeError(
                "Hermes provider unsupported. Use one of: openai, azure, anthropic, gemini, google"
            )

    if provider in {"gemini", "google"}:
        if not settings.gemini_api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is required for Hermes dashboard with gemini provider"
            )
        os.environ.setdefault("GEMINI_API_KEY", settings.gemini_api_key)

    return Agent(
        provider=provider,
        model=settings.hermes_model,
        name="ArcvoDashboard",
        description="Operational dashboard assistant for Arcvo",
        prompt=_build_dashboard_prompt(),
        tools=[
            ArcvoDashboardTools.system_context,
            ArcvoDashboardTools.list_agents,
            ArcvoDashboardTools.list_agent_audit,
            ArcvoDashboardTools.assign_task,
            ArcvoDashboardTools.run_pending,
            ArcvoDashboardTools.run_agent,
            ArcvoDashboardTools.get_production_status,
            ArcvoDashboardTools.get_odoo_health,
        ],
        max_chat_history_length=30,
        temperature=0.2,
    )


async def run_dashboard() -> None:
    from hermes.web import hermes_web

    agent = create_dashboard_agent()
    await hermes_web(port=settings.hermes_dashboard_port, agent=agent)
