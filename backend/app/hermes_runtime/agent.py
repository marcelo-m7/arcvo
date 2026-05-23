"""
Hermes Agent - Individual autonomous agent model
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, Callable, Awaitable
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class AgentState(str, Enum):
    """Agent operational states."""
    IDLE = "idle"
    READY = "ready"
    BUSY = "busy"
    THINKING = "thinking"
    ACTING = "acting"
    ERROR = "error"
    OFFLINE = "offline"

class AgentRole(str, Enum):
    """Predefined agent roles in the digital company."""
    CEO = "ceo"
    PROJECT_MANAGER = "project_manager"
    BACKEND_DEVELOPER = "backend_developer"
    FRONTEND_DEVELOPER = "frontend_developer"
    DEVOPS = "devops"
    QA_TESTER = "qa_tester"
    DOCUMENTATION = "documentation"
    ODOO_SPECIALIST = "odoo_specialist"
    ACADEMIC_IMPORTER = "academic_importer"

@dataclass
class Agent:
    """Autonomous agent in Hermes framework."""
    
    # Identity
    agent_id: int
    name: str
    role: AgentRole
    description: str = ""
    
    # Capabilities
    capabilities: list[str] = field(default_factory=list)
    
    # Performance
    state: AgentState = AgentState.IDLE
    current_task_id: Optional[int] = None
    workload: int = 0
    max_workload: int = 3
    
    # Odoo Integration
    odoo_project_id: Optional[int] = None
    api_key: str = ""
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_heartbeat: Optional[datetime] = None
    
    # Stats
    tasks_completed: int = 0
    tasks_failed: int = 0
    total_runtime_minutes: float = 0.0
    
    # Registry reference
    registry: Optional[Any] = None
    
    async def execute_task(self, task: dict[str, Any]) -> dict[str, Any]:
        """Execute a task assigned to this agent."""
        try:
            self.state = AgentState.THINKING
            task_id = task.get("id")
            
            logger.info(f"🤖 {self.name} thinking about task {task_id}...")
            
            # TODO: Implement task execution logic based on role
            match self.role:
                case AgentRole.BACKEND_DEVELOPER:
                    result = await self._execute_backend_task(task)
                case AgentRole.FRONTEND_DEVELOPER:
                    result = await self._execute_frontend_task(task)
                case AgentRole.DEVOPS:
                    result = await self._execute_devops_task(task)
                case _:
                    result = {"status": "not_implemented"}
            
            self.tasks_completed += 1
            self.state = AgentState.READY
            return result
            
        except Exception as e:
            logger.error(f"❌ {self.name} failed task {task.get('id')}: {e}")
            self.tasks_failed += 1
            self.state = AgentState.ERROR
            return {"status": "failed", "error": str(e)}
    
    async def _execute_backend_task(self, task: dict[str, Any]) -> dict[str, Any]:
        """Backend developer execution."""
        logger.info(f"💻 Backend task: {task.get('description')}")
        # TODO: Implement backend-specific logic
        return {"status": "in_progress"}
    
    async def _execute_frontend_task(self, task: dict[str, Any]) -> dict[str, Any]:
        """Frontend developer execution."""
        logger.info(f"🎨 Frontend task: {task.get('description')}")
        # TODO: Implement frontend-specific logic
        return {"status": "in_progress"}
    
    async def _execute_devops_task(self, task: dict[str, Any]) -> dict[str, Any]:
        """DevOps execution."""
        logger.info(f"🚀 DevOps task: {task.get('description')}")
        # TODO: Implement DevOps-specific logic
        return {"status": "in_progress"}
    
    def report_heartbeat(self) -> dict[str, Any]:
        """Send heartbeat to Odoo."""
        self.last_heartbeat = datetime.now()
        
        if self.registry and hasattr(self.registry, 'odoo_client'):
            try:
                self.registry.odoo_client.write(
                    "agent.agent",
                    self.agent_id,
                    {
                        "last_heartbeat": self.last_heartbeat.isoformat(),
                        "status": self.state.value,
                        "current_workload": self.workload,
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to report heartbeat: {e}")
        
        return {
            "agent_id": self.agent_id,
            "state": self.state.value,
            "timestamp": self.last_heartbeat.isoformat(),
        }
    
    def is_available(self) -> bool:
        """Check if agent can accept new tasks."""
        return (
            self.state in [AgentState.IDLE, AgentState.READY]
            and self.workload < self.max_workload
        )
    
    def __str__(self) -> str:
        return f"{self.name} ({self.role.value}) - {self.state.value}"
