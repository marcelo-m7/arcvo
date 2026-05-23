"""FastAPI routes for hermes-ai agent interaction."""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.core.security import require_admin
from app.hermes_runtime.agents import create_task_agent, get_provider_config
from app.hermes_runtime.tools import (
    create_odoo_task,
    get_odoo_task,
    list_odoo_agents,
    list_odoo_projects,
    list_odoo_tasks,
)

logger = logging.getLogger(__name__)

router = APIRouter()


class ChatRequest(BaseModel):
    """User message for agent processing."""

    message: str = Field(..., min_length=1, max_length=1000)


class ChatResponse(BaseModel):
    """Agent response with metadata."""

    response: str
    provider: str
    model: str
    tokens_used: int | None = None


class StatusResponse(BaseModel):
    """Hermes runtime status."""

    configured: bool
    provider: str | None = None
    model: str | None = None
    has_odoo: bool = False
    has_llm: bool = False
    tools_available: list[str] = []


@router.get(
    "/status",
    response_model=StatusResponse,
    summary="Get Hermes runtime status",
    tags=["hermes"],
)
async def get_hermes_status(settings=Depends(get_settings)) -> StatusResponse:
    """Check Hermes configuration and availability."""
    provider = None
    model = None

    try:
        provider, model, _ = get_provider_config(settings)
    except ValueError:
        pass

    return StatusResponse(
        configured=bool(provider),
        provider=provider,
        model=model,
        has_odoo=settings.has_odoo_credentials,
        has_llm=settings.has_llm_configured,
        tools_available=[
            "list_odoo_projects",
            "list_odoo_tasks",
            "get_odoo_task",
            "create_odoo_task",
            "list_odoo_agents",
        ],
    )


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=200,
    summary="Execute agent task with message",
    tags=["hermes"],
)
async def hermes_chat(
    request: ChatRequest,
    _=Depends(require_admin),
    settings=Depends(get_settings),
) -> ChatResponse:
    """Send a message to the Hermes agent for processing.

    The agent will use available Odoo tools to answer questions, retrieve
    data, or execute tasks. Requires admin authentication.

    Args:
        request: User message and context.
        settings: FastAPI settings (auto-injected).

    Returns:
        Agent response with provider and model metadata.

    Raises:
        HTTPException(503): If LLM not configured or Odoo unreachable.
        HTTPException(400): If no valid provider.
    """
    # Validate configuration
    if not settings.has_llm_configured:
        logger.error("❌ No LLM provider configured")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM provider not configured. Set GEMINI_API_KEY or OPENROUTER_API_KEY.",
        )

    try:
        provider, model, _ = get_provider_config(settings)
    except ValueError as exc:
        logger.error(f"Provider config error: {exc}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    # Create agent with tools
    try:
        agent = create_task_agent(
            settings,
            tools=[
                list_odoo_projects,
                list_odoo_tasks,
                get_odoo_task,
                create_odoo_task,
                list_odoo_agents,
            ],
        )
    except Exception as exc:
        logger.error(f"Failed to create agent: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to initialize agent: {exc}",
        ) from exc

    # Execute agent
    try:
        logger.info(f"🚀 Executing agent task: {request.message[:100]}")
        import asyncio

        response = await agent.execute(input_data=request.message)
        logger.info(f"✅ Agent response received ({len(str(response))} chars)")

        return ChatResponse(
            response=str(response),
            provider=provider,
            model=model,
            tokens_used=None,  # hermes-ai doesn't expose token usage yet
        )
    except Exception as exc:
        logger.error(f"❌ Agent execution failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Agent execution failed: {exc}",
        ) from exc
