"""Create and manage hermes-ai agents for task execution."""
from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


def get_provider_config(settings: Any) -> tuple[str, str, str]:
    """Determine the LLM provider and model based on configured API keys.

    Priority:
    1. Gemini (if GEMINI_API_KEY is set)
    2. OpenRouter (if OPENROUTER_API_KEY is set)

    Args:
        settings: FastAPI Settings object with API keys.

    Returns:
        Tuple of (provider, model, api_key).

    Raises:
        ValueError: If no LLM provider is configured.
    """
    if settings.gemini_api_key:
        return ("gemini", "gemini-2.0-flash", settings.gemini_api_key)

    if settings.openrouter_api_key:
        # Set OpenAI base URL for OpenRouter compatibility
        os.environ["OPENAI_BASE_URL"] = "https://openrouter.ai/api/v1"
        return ("openai", "google/gemini-flash-1.5", settings.openrouter_api_key)

    raise ValueError(
        "No LLM provider configured. Set GEMINI_API_KEY or OPENROUTER_API_KEY in .env"
    )


def create_task_agent(settings: Any, tools: list | None = None) -> Any:
    """Create a hermes-ai Agent configured for task execution in Odoo context.

    Args:
        settings: FastAPI Settings with LLM API keys.
        tools: Optional list of tool functions to attach to the agent.

    Returns:
        A hermes-ai Agent instance ready to execute tasks.

    Raises:
        ValueError: If no LLM provider is configured.
    """
    from hermes.core import Agent

    if tools is None:
        tools = []

    provider, model, api_key = get_provider_config(settings)

    system_prompt = """You are an AI agent working within Monynha Softwares' Arcvo platform.
Your primary responsibilities:
1. Manage tasks and projects in Odoo 19
2. Execute work autonomously based on assigned tasks
3. Report progress and blockers back to the system

**Context:**
- Organization: Monynha Softwares, Odoo 19 ERP at https://marcelo-m7.com
- Platform: Arcvo (agent execution + archive course management)
- Tools available: Odoo project/task management, agent registry queries

**Behavior:**
- Be concise and action-oriented
- Use provided tools to fetch/update Odoo data
- Always report task completion or blockers
- Format responses in JSON when returning structured data

**Language:** Portuguese-BR when user context requires, English otherwise."""

    agent = Agent(
        provider=provider,
        model=model,
        api_key=api_key,
        name="Arcvo Task Agent",
        description="Autonomous agent for task execution in Odoo 19",
        prompt=system_prompt,
        tools=tools,
        temperature=0.7,
        max_chat_history_length=20,
        token_limit=4000,
        debug=settings.is_development,
    )

    logger.info(
        f"✅ Task Agent created: provider={provider}, model={model}, tools={len(tools)}"
    )
    return agent
