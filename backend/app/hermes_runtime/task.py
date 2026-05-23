"""
Hermes Task - Task model for agent coordination
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional
from datetime import datetime

class TaskStatus(str, Enum):
    """Task lifecycle states."""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    REVIEW = "review"
    DONE = "done"
    FAILED = "failed"

class TaskPriority(str, Enum):
    """Task priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class Task:
    """A task in the Hermes execution queue."""
    
    # Identity
    task_id: int
    name: str
    description: str
    project_id: int
    
    # Status
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    
    # Assignment
    assigned_agent_id: Optional[int] = None
    created_by: str = "system"
    
    # Requirements
    required_capabilities: list[str] = field(default_factory=list)
    estimated_hours: float = 0.0
    
    # Tracking
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    due_date: Optional[datetime] = None
    
    # Progress
    progress_percentage: int = 0
    notes: str = ""
    result: dict[str, Any] = field(default_factory=dict)
    
    # Odoo reference
    odoo_task_id: Optional[int] = None
    
    def can_be_assigned_to_agent(self, agent) -> bool:
        """Check if task can be assigned to an agent."""
        # Check if agent has required capabilities
        if self.required_capabilities:
            agent_caps = set(agent.capabilities)
            required_caps = set(self.required_capabilities)
            if not required_caps.issubset(agent_caps):
                return False
        
        # Check if agent is available
        if not agent.is_available():
            return False
        
        return True
    
    def mark_started(self) -> None:
        """Mark task as started."""
        if self.status == TaskStatus.TODO:
            self.status = TaskStatus.IN_PROGRESS
            self.started_at = datetime.now()
    
    def mark_completed(self, result: dict[str, Any]) -> None:
        """Mark task as completed."""
        self.status = TaskStatus.DONE
        self.completed_at = datetime.now()
        self.progress_percentage = 100
        self.result = result
    
    def mark_failed(self, error: str) -> None:
        """Mark task as failed."""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.now()
        self.result = {"error": error}
    
    def get_elapsed_minutes(self) -> float:
        """Get elapsed time in minutes."""
        if self.started_at:
            end_time = self.completed_at or datetime.now()
            elapsed = end_time - self.started_at
            return elapsed.total_seconds() / 60.0
        return 0.0
    
    def __str__(self) -> str:
        return f"Task #{self.task_id}: {self.name} ({self.status.value})"
