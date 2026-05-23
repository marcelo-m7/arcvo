"""
Hermes Agent Framework - Autonomous Agent Runtime

Hermes is the autonomous execution layer for the digital company.
It coordinates agents, manages task delegation, and integrates with Odoo.
"""

__version__ = "0.1.0"
__author__ = "Monynha Digital"

from .core import HermesCore, HermesConfig, HermesState
from .agent import Agent, AgentState, AgentRole
from .task import Task, TaskStatus, TaskPriority
from .registry import AgentRegistry, create_default_agents

__all__ = [
    "HermesCore",
    "HermesConfig",
    "HermesState",
    "Agent",
    "AgentState",
    "AgentRole",
    "Task",
    "TaskStatus",
    "TaskPriority",
    "AgentRegistry",
    "create_default_agents",
]
