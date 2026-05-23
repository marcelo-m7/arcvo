#!/usr/bin/env python3
"""
Hermes Agent Discovery and Installation Script

This script:
1. Checks if hermes-agent is available via pip
2. Installs hermes-agent if needed
3. Tests basic Hermes functionality
4. Creates a wrapper for Odoo integration
"""

import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    """Run a command and report results."""
    print(f"\n{'='*60}")
    print(f"🔍 {description}")
    print(f"{'='*60}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🚀 Hermes Agent Setup\n")
    
    # Step 1: Check if hermes-agent is available via pip search
    print("Step 1: Checking for hermes-agent package...")
    
    # Try to install hermes-agent
    # Note: hermes-agent might be called different names. Common variants:
    # - hermes-agent
    # - hermes
    # - hermes-py
    # - agent-hermes
    
    candidates = [
        ("hermes-agent", "pip install hermes-agent"),
        ("hermes", "pip install hermes"),
        ("anthropic-agent", "pip install anthropic"),  # Common agent framework
    ]
    
    hermes_installed = False
    for package_name, install_cmd in candidates:
        print(f"\n   Trying: {package_name}...")
        result = subprocess.run(
            f"{sys.executable} -m pip show {package_name}",
            shell=True,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"   ✅ {package_name} is already installed!")
            print(result.stdout[:200])
            hermes_installed = True
            break
    
    if not hermes_installed:
        print("\n⚠️  Hermes Agent not found in standard Python packages.")
        print("   Hermes Agent might be:")
        print("   1. A custom framework (not published)")
        print("   2. Available via custom source")
        print("   3. Named differently")
        print("\n   Proceeding with alternative approach:")
        print("   - Building Hermes as OpenAI-compatible agent framework")
        print("   - Using existing Odoo integration")
    
    # Step 2: Check what agent frameworks ARE available
    print("\n\nStep 2: Checking available agent frameworks...")
    frameworks = {
        "anthropic": "pip install anthropic",
        "openai": "pip install openai",
        "langchain": "pip install langchain",
        "crewai": "pip install crewai",
    }
    
    available = []
    for framework, install_cmd in frameworks.items():
        result = subprocess.run(
            f"{sys.executable} -m pip show {framework}",
            shell=True,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            available.append(framework)
    
    print(f"\n✅ Available frameworks: {', '.join(available) if available else 'None'}")
    
    # Step 3: Test direct Hermes import
    print("\n\nStep 3: Attempting direct Hermes import...")
    try:
        import hermes
        print("✅ Hermes imported successfully!")
        print(f"   Version: {getattr(hermes, '__version__', 'unknown')}")
        print(f"   Location: {hermes.__file__}")
    except ImportError as e:
        print(f"❌ Hermes import failed: {e}")
    
    # Step 4: Create Hermes wrapper
    print("\n\nStep 4: Creating Hermes-Odoo integration wrapper...")
    
    wrapper_code = '''"""
Hermes Agent - Odoo Integration Wrapper

This module provides a unified interface for Hermes agents to operate on Odoo tasks.
"""

from typing import Any, dict, list, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class HermesAgentConfig:
    """Configuration for a Hermes agent."""
    agent_id: int
    name: str
    role: str
    capabilities: list[str]
    odoo_project_id: Optional[int] = None
    max_concurrent_tasks: int = 1

class HermesOdooAgent:
    """Base class for Hermes agents operating on Odoo."""
    
    def __init__(self, config: HermesAgentConfig, odoo_client=None):
        self.config = config
        self.odoo_client = odoo_client
        self.current_task = None
        self.task_log = []
    
    def get_pending_tasks(self) -> list[dict[str, Any]]:
        """Fetch pending tasks from Odoo based on capabilities."""
        if not self.odoo_client:
            return []
        
        # TODO: Query Odoo for tasks matching agent's capabilities
        pass
    
    def claim_task(self, task_id: int) -> bool:
        """Claim a task from Odoo."""
        if not self.odoo_client:
            return False
        
        # TODO: Create assignment in agent_registry
        pass
    
    def report_progress(self, progress: int, notes: str = "") -> bool:
        """Report task progress to Odoo."""
        if not self.odoo_client:
            return False
        
        # TODO: Update agent_assignment with progress
        pass
    
    def complete_task(self, result: dict[str, Any]) -> bool:
        """Mark task as complete."""
        if not self.odoo_client:
            return False
        
        # TODO: Update task status, create result record
        pass

# Predefined agents matching organization structure
HERMES_AGENTS = {
    "ceo": HermesAgentConfig(
        agent_id=1,
        name="CEO Agent",
        role="Strategic coordination",
        capabilities=["strategic_planning", "decision_making", "reporting"]
    ),
    "pm": HermesAgentConfig(
        agent_id=2,
        name="Project Manager Agent",
        role="Task orchestration",
        capabilities=["project_management", "task_delegation", "monitoring"]
    ),
    "backend": HermesAgentConfig(
        agent_id=3,
        name="Backend Developer Agent",
        role="API and service development",
        capabilities=["python", "api_development", "database"]
    ),
    "frontend": HermesAgentConfig(
        agent_id=4,
        name="Frontend Developer Agent",
        role="UI/UX implementation",
        capabilities=["typescript", "react", "frontend"]
    ),
    "devops": HermesAgentConfig(
        agent_id=5,
        name="DevOps Agent",
        role="Infrastructure and deployment",
        capabilities=["docker", "kubernetes", "ci_cd"]
    ),
}

async def initialize_hermes(odoo_client) -> dict[str, HermesOdooAgent]:
    """Initialize all Hermes agents with Odoo client."""
    agents = {}
    for agent_key, config in HERMES_AGENTS.items():
        agent = HermesOdooAgent(config, odoo_client)
        agents[agent_key] = agent
    return agents
'''
    
    wrapper_path = Path("backend/app/agents/hermes.py")
    wrapper_path.parent.mkdir(parents=True, exist_ok=True)
    wrapper_path.write_text(wrapper_code)
    
    print(f"✅ Created: {wrapper_path}")
    print(f"   Location: {wrapper_path.resolve()}")

if __name__ == "__main__":
    main()
