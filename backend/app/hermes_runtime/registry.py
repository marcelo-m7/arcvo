"""
Hermes Agent Registry - Central agent management
"""

from typing import Any, Optional
import logging
from datetime import datetime

from .agent import Agent, AgentRole, AgentState

logger = logging.getLogger(__name__)

class AgentRegistry:
    """Central registry and coordinator for all Hermes agents."""
    
    def __init__(self, odoo_client: Optional[Any] = None):
        self.agents: dict[int, Agent] = {}
        self.agents_by_role: dict[AgentRole, list[Agent]] = {
            role: [] for role in AgentRole
        }
        self.odoo_client = odoo_client
    
    def register_agent(self, agent: Agent) -> None:
        """Register a new agent."""
        self.agents[agent.agent_id] = agent
        agent.registry = self
        self.agents_by_role[agent.role].append(agent)
        logger.info(f"✅ Registered: {agent}")
    
    def get_agent(self, agent_id: int) -> Optional[Agent]:
        """Get agent by ID."""
        return self.agents.get(agent_id)
    
    def get_agents_by_role(self, role: AgentRole) -> list[Agent]:
        """Get all agents with a specific role."""
        return self.agents_by_role.get(role, [])
    
    def get_available_agents(self) -> list[Agent]:
        """Get all available agents."""
        return [a for a in self.agents.values() if a.is_available()]
    
    def find_best_agent_for_task(self, task: Any) -> Optional[Agent]:
        """Find the best agent to handle a task based on capabilities."""
        candidates = []
        
        # Filter agents with required capabilities
        for agent in self.agents.values():
            if task.can_be_assigned_to_agent(agent):
                candidates.append(agent)
        
        if not candidates:
            return None
        
        # Sort by workload (prefer less busy agents)
        candidates.sort(key=lambda a: a.workload)
        return candidates[0]
    
    async def load_from_odoo(self) -> bool:
        """Load agent registry from Odoo."""
        if not self.odoo_client:
            logger.warning("No Odoo client configured")
            return False
        
        try:
            logger.info("📥 Loading agents from Odoo...")
            
            # Search for agent records in Odoo
            agent_records = self.odoo_client.search_read(
                "agent.agent",
                fields=[
                    "id", "name", "agent_type", "status",
                    "current_workload", "max_concurrent_tasks",
                    "capabilities_ids", "last_heartbeat"
                ],
                limit=100
            )
            
            for record in agent_records:
                # Map Odoo agent_type to AgentRole
                role_mapping = {
                    "ceo": AgentRole.CEO,
                    "project_manager": AgentRole.PROJECT_MANAGER,
                    "backend_developer": AgentRole.BACKEND_DEVELOPER,
                    "frontend_developer": AgentRole.FRONTEND_DEVELOPER,
                    "devops": AgentRole.DEVOPS,
                    "qa_tester": AgentRole.QA_TESTER,
                    "documentation": AgentRole.DOCUMENTATION,
                    "odoo_specialist": AgentRole.ODOO_SPECIALIST,
                }
                
                role = role_mapping.get(record.get("agent_type", ""), AgentRole.BACKEND_DEVELOPER)
                
                agent = Agent(
                    agent_id=record["id"],
                    name=record["name"],
                    role=role,
                    capabilities=record.get("capabilities_ids", []),
                    state=AgentState(record.get("status", "idle")),
                    workload=record.get("current_workload", 0),
                    max_workload=record.get("max_concurrent_tasks", 1),
                )
                
                self.register_agent(agent)
            
            logger.info(f"✅ Loaded {len(self.agents)} agents from Odoo")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to load agents from Odoo: {e}")
            return False
    
    def get_status(self) -> dict[str, Any]:
        """Get registry status."""
        available = len(self.get_available_agents())
        total = len(self.agents)
        
        agents_by_state = {}
        for agent in self.agents.values():
            state = agent.state.value
            agents_by_state[state] = agents_by_state.get(state, 0) + 1
        
        return {
            "total_agents": total,
            "available_agents": available,
            "agents_by_state": agents_by_state,
            "agents_by_role": {
                role.value: len(agents)
                for role, agents in self.agents_by_role.items()
                if agents
            },
        }
    
    def __repr__(self) -> str:
        return f"AgentRegistry({len(self.agents)} agents)"


# Factory for creating predefined agents
def create_default_agents(odoo_client: Optional[Any] = None) -> AgentRegistry:
    """Create a registry with predefined agents for a digital company."""
    registry = AgentRegistry(odoo_client)
    
    agents_config = [
        {
            "id": 1,
            "name": "CEO",
            "role": AgentRole.CEO,
            "capabilities": ["strategic_planning", "decision_making", "reporting"],
        },
        {
            "id": 2,
            "name": "Project Manager",
            "role": AgentRole.PROJECT_MANAGER,
            "capabilities": ["project_management", "task_delegation", "monitoring"],
        },
        {
            "id": 3,
            "name": "Backend Developer",
            "role": AgentRole.BACKEND_DEVELOPER,
            "capabilities": ["python", "api_development", "database", "testing"],
        },
        {
            "id": 4,
            "name": "Frontend Developer",
            "role": AgentRole.FRONTEND_DEVELOPER,
            "capabilities": ["typescript", "react", "ui_design", "testing"],
        },
        {
            "id": 5,
            "name": "DevOps",
            "role": AgentRole.DEVOPS,
            "capabilities": ["docker", "deployment", "ci_cd", "monitoring"],
        },
        {
            "id": 6,
            "name": "QA Tester",
            "role": AgentRole.QA_TESTER,
            "capabilities": ["testing", "automation", "validation"],
        },
        {
            "id": 7,
            "name": "Documentation",
            "role": AgentRole.DOCUMENTATION,
            "capabilities": ["documentation", "writing", "technical_analysis"],
        },
        {
            "id": 8,
            "name": "Odoo Specialist",
            "role": AgentRole.ODOO_SPECIALIST,
            "capabilities": ["odoo_development", "module_creation", "customization"],
        },
    ]
    
    for config in agents_config:
        agent = Agent(
            agent_id=config["id"],
            name=config["name"],
            role=config["role"],
            capabilities=config["capabilities"],
            description=f"Autonomous {config['role'].value} agent",
        )
        registry.register_agent(agent)
    
    return registry
