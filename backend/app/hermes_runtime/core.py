"""
Hermes Core - Main orchestration engine
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Optional
from datetime import datetime
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class HermesState(str, Enum):
    """Hermes runtime states."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    SHUTDOWN = "shutdown"

@dataclass
class HermesConfig:
    """Hermes configuration."""
    odoo_url: str
    odoo_db: str
    odoo_user: str
    odoo_api_key: str = ""
    integration_mode: str = "xmlrpc"  # xmlrpc or jsonrpc
    allow_self_signed_ssl: bool = False
    polling_interval: int = 60  # seconds
    max_retries: int = 3
    debug: bool = False

class HermesCore:
    """Core Hermes orchestration engine."""
    
    def __init__(self, config: HermesConfig):
        self.config = config
        self.state = HermesState.IDLE
        self.agents: dict[str, Any] = {}
        self.tasks: list[dict[str, Any]] = []
        self.started_at: Optional[datetime] = None
        self.odoo_client = None
        
        if config.debug:
            logging.basicConfig(level=logging.DEBUG)
        
        logger.info(f"Hermes initialized: {config.odoo_url}/{config.odoo_db}")
    
    async def start(self) -> bool:
        """Start Hermes runtime."""
        try:
            logger.info("🚀 Starting Hermes...")
            self.state = HermesState.RUNNING
            self.started_at = datetime.now()
            
            # Initialize Odoo client
            from app.integrations.odoo.client import OdooClient, OdooCredentials
            
            credentials = OdooCredentials(
                url=self.config.odoo_url,
                database=self.config.odoo_db,
                username=self.config.odoo_user,
                api_key=self.config.odoo_api_key,
                allow_self_signed_ssl=self.config.allow_self_signed_ssl,
            )
            self.odoo_client = OdooClient(credentials)
            self.odoo_client.authenticate()
            
            logger.info("✅ Odoo connection established")
            logger.info(f"   User: {self.config.odoo_user} (UID: {self.odoo_client.uid})")
            
            return True
        except Exception as e:
            logger.error(f"❌ Failed to start Hermes: {e}")
            self.state = HermesState.ERROR
            return False
    
    async def stop(self) -> None:
        """Stop Hermes runtime."""
        logger.info("🛑 Stopping Hermes...")
        self.state = HermesState.SHUTDOWN
    
    def register_agent(self, agent_key: str, agent: Any) -> None:
        """Register an agent with Hermes."""
        self.agents[agent_key] = agent
        logger.info(f"✅ Registered agent: {agent_key}")
    
    async def dispatch_task(self, task: dict[str, Any]) -> bool:
        """Dispatch a task to an appropriate agent."""
        try:
            logger.info(f"📋 Dispatching task: {task.get('name')}")
            # TODO: Implement task routing logic
            return True
        except Exception as e:
            logger.error(f"❌ Task dispatch failed: {e}")
            return False
    
    def get_status(self) -> dict[str, Any]:
        """Get Hermes runtime status."""
        uptime_seconds = None
        if self.started_at:
            uptime_seconds = (datetime.now() - self.started_at).total_seconds()
        
        return {
            "state": self.state.value,
            "agents": len(self.agents),
            "active_tasks": len(self.tasks),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "uptime_seconds": uptime_seconds,
            "odoo_connected": self.odoo_client is not None,
        }
