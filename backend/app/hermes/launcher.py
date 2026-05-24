from __future__ import annotations

import os

from app.core.config import settings
from app.hermes.tools import ArcvoHermesTools

SUPPORTED_HERMES_PROVIDERS = {"openai", "azure", "anthropic", "gemini", "google"}


def _build_prompt() -> str:
    return (
        "You are Arcvo Operations Assistant. Respond in Portuguese with concise, "
        "operational guidance. Odoo is the single source of truth: always use tools "
        "before claiming record state, and every state-changing action must be "
        "registered in Odoo. Never include secrets, tokens, passwords, API keys, or "
        "environment values in prompts, tool outputs, chat replies, or audit notes."
    )


def create_hermes_agent():
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
            raise RuntimeError("GEMINI_API_KEY is required for Hermes with gemini/google provider")
        os.environ.setdefault("GEMINI_API_KEY", settings.gemini_api_key)

    return Agent(
        provider=provider,
        model=settings.hermes_model,
        name="ArcvoOdooOps",
        description="Odoo-backed operational assistant for Arcvo",
        prompt=_build_prompt(),
        tools=[
            ArcvoHermesTools.system_context,
            ArcvoHermesTools.list_agents,
            ArcvoHermesTools.list_agent_audit,
            ArcvoHermesTools.assign_task,
            ArcvoHermesTools.send_agent_message,
            ArcvoHermesTools.list_agent_messages,
            ArcvoHermesTools.run_pending,
            ArcvoHermesTools.run_agent,
            ArcvoHermesTools.get_production_status,
            ArcvoHermesTools.get_odoo_health,
        ],
        max_chat_history_length=30,
        temperature=0.2,
    )


async def run_hermes() -> None:
    from hermes.web import hermes_web

    agent = create_hermes_agent()
    await hermes_web(port=settings.hermes_dashboard_port, agent=agent)

