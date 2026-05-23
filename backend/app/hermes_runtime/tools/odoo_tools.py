"""Odoo tool functions for hermes-ai agents.

Plain synchronous Python functions auto-converted to LlamaIndex FunctionTools.
Each function returns a human-readable string for the LLM.
"""
from __future__ import annotations

import json
import logging

logger = logging.getLogger(__name__)


def _get_odoo_client():
    """Create and authenticate an OdooClient from current settings."""
    from app.core.config import get_settings
    from app.integrations.odoo.client import OdooClient, OdooCredentials

    s = get_settings()
    if not s.has_odoo_credentials:
        raise RuntimeError("Odoo credentials not configured.")
    creds = OdooCredentials(
        url=s.odoo_url,
        database=s.odoo_db,
        username=s.odoo_user,
        api_key=s.odoo_api_key,
        allow_self_signed_ssl=s.odoo_allow_self_signed_ssl,
    )
    client = OdooClient(creds)
    client.authenticate()
    return client


def list_odoo_projects(limit: int = 10) -> str:
    """List active projects from Odoo.

    Args:
        limit: Maximum number of projects to return (default 10).

    Returns:
        JSON-formatted list of projects with id, name, and task count.
    """
    try:
        client = _get_odoo_client()
        records = client.search_read(
            "project.project",
            domain=[["active", "=", True]],
            fields=["id", "name", "task_count"],
            limit=limit,
        )
        if not records:
            return "No active projects found in Odoo."
        lines = [f"Found {len(records)} project(s):"]
        for r in records:
            lines.append(f"  - [{r['id']}] {r['name']} ({r.get('task_count', 0)} tasks)")
        return "\n".join(lines)
    except Exception as exc:
        logger.error("list_odoo_projects failed: %s", exc)
        return f"Error listing projects: {exc}"


def list_odoo_tasks(project_name: str = "", limit: int = 10) -> str:
    """List tasks from Odoo, optionally filtered by project name.

    Args:
        project_name: Optional project name to filter tasks (partial match).
        limit: Maximum number of tasks to return (default 10).

    Returns:
        Formatted list of tasks with id, name, stage, and assignee.
    """
    try:
        client = _get_odoo_client()
        domain: list = [["active", "=", True]]
        if project_name:
            domain.append(["project_id.name", "ilike", project_name])
        records = client.search_read(
            "project.task",
            domain=domain,
            fields=["id", "name", "stage_id", "user_ids", "project_id"],
            limit=limit,
        )
        if not records:
            return f"No tasks found{f' for project \"{project_name}\"' if project_name else ''}."
        lines = [f"Found {len(records)} task(s):"]
        for r in records:
            project = r.get("project_id", [None, "No project"])
            stage = r.get("stage_id", [None, "No stage"])
            lines.append(
                f"  - [{r['id']}] {r['name']} | "
                f"Project: {project[1] if project else '-'} | "
                f"Stage: {stage[1] if stage else '-'}"
            )
        return "\n".join(lines)
    except Exception as exc:
        logger.error("list_odoo_tasks failed: %s", exc)
        return f"Error listing tasks: {exc}"


def get_odoo_task(task_id: int) -> str:
    """Get detailed information about a specific Odoo task.

    Args:
        task_id: The numeric ID of the task to retrieve.

    Returns:
        Detailed task information including description, stage, and assignees.
    """
    try:
        client = _get_odoo_client()
        records = client.search_read(
            "project.task",
            domain=[["id", "=", task_id]],
            fields=["id", "name", "description", "stage_id", "user_ids", "project_id", "priority"],
            limit=1,
        )
        if not records:
            return f"Task with ID {task_id} not found."
        r = records[0]
        project = r.get("project_id", [None, "No project"])
        stage = r.get("stage_id", [None, "No stage"])
        desc = r.get("description") or "(no description)"
        # Strip HTML tags simply
        import re
        desc = re.sub(r"<[^>]+>", "", desc).strip()[:500]
        return (
            f"Task [{r['id']}]: {r['name']}\n"
            f"Project: {project[1] if project else '-'}\n"
            f"Stage: {stage[1] if stage else '-'}\n"
            f"Priority: {'High' if r.get('priority') == '1' else 'Normal'}\n"
            f"Description: {desc}"
        )
    except Exception as exc:
        logger.error("get_odoo_task failed: %s", exc)
        return f"Error fetching task {task_id}: {exc}"


def create_odoo_task(name: str, project_name: str, description: str = "") -> str:
    """Create a new task in an Odoo project.

    Args:
        name: Task name/title.
        project_name: Exact or partial name of the project to create the task in.
        description: Optional task description.

    Returns:
        Confirmation message with the new task ID, or an error message.
    """
    try:
        client = _get_odoo_client()
        # Find project by name
        projects = client.search_read(
            "project.project",
            domain=[["name", "ilike", project_name], ["active", "=", True]],
            fields=["id", "name"],
            limit=1,
        )
        if not projects:
            return f"Project '{project_name}' not found in Odoo."
        project = projects[0]
        values: dict = {"name": name, "project_id": project["id"]}
        if description:
            values["description"] = f"<p>{description}</p>"
        task_id = client.create("project.task", values)
        return f"Task created successfully: [{task_id}] \"{name}\" in project \"{project['name']}\"."
    except Exception as exc:
        logger.error("create_odoo_task failed: %s", exc)
        return f"Error creating task: {exc}"


def list_odoo_agents(limit: int = 10) -> str:
    """List registered AI agents from the Odoo agent registry.

    Args:
        limit: Maximum number of agents to return (default 10).

    Returns:
        Formatted list of agents with id, name, role, and status.
    """
    try:
        client = _get_odoo_client()
        records = client.search_read(
            "agent.agent",
            domain=[],
            fields=["id", "name", "role", "state"],
            limit=limit,
        )
        if not records:
            return "No agents found in the Odoo agent registry."
        lines = [f"Found {len(records)} agent(s):"]
        for r in records:
            lines.append(
                f"  - [{r['id']}] {r['name']} | Role: {r.get('role', '-')} | State: {r.get('state', '-')}"
            )
        return "\n".join(lines)
    except Exception as exc:
        logger.error("list_odoo_agents failed: %s", exc)
        return f"Error listing agents: {exc}"
