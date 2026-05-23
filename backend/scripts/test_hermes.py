#!/usr/bin/env python3
"""
Hermes Agent Test Suite

Tests:
1. Hermes can be imported
2. Hermes can initialize with config
3. Hermes can load agents from Odoo
4. Agents can execute tasks
5. Status tracking works
"""

import asyncio
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_hermes_import():
    """Test 1: Import Hermes."""
    print("\n" + "="*60)
    print("TEST 1: Import Hermes Framework")
    print("="*60)
    
    try:
        from app.hermes_runtime import (
            HermesCore, HermesConfig, HermesState,
            Agent, AgentRole, AgentState,
            Task, TaskStatus,
            AgentRegistry, create_default_agents
        )
        print("✅ All Hermes components imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

async def test_hermes_init():
    """Test 2: Initialize Hermes with config."""
    print("\n" + "="*60)
    print("TEST 2: Initialize Hermes with Configuration")
    print("="*60)
    
    try:
        from app.hermes_runtime import HermesCore, HermesConfig
        from app.core.config import get_settings
        
        settings = get_settings()
        
        config = HermesConfig(
            odoo_url=settings.odoo_url,
            odoo_db=settings.odoo_db,
            odoo_user=settings.odoo_user or "admin",
            odoo_api_key=settings.odoo_api_key or "",
            integration_mode="xmlrpc",
            debug=True
        )
        
        hermes = HermesCore(config)
        print(f"✅ Hermes initialized: {config.odoo_url}/{config.odoo_db}")
        print(f"   State: {hermes.state.value}")
        return True, hermes
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None

async def test_hermes_start(hermes):
    """Test 3: Start Hermes and connect to Odoo."""
    print("\n" + "="*60)
    print("TEST 3: Start Hermes and Connect to Odoo")
    print("="*60)
    
    try:
        success = await hermes.start()
        if success:
            print(f"✅ Hermes started successfully")
            status = hermes.get_status()
            print(f"   Status: {status}")
            return True, hermes
        else:
            print("❌ Hermes failed to start")
            return False, hermes
    except Exception as e:
        print(f"❌ Start failed: {e}")
        import traceback
        traceback.print_exc()
        return False, hermes

async def test_agent_registry(hermes):
    """Test 4: Create and manage agent registry."""
    print("\n" + "="*60)
    print("TEST 4: Agent Registry and Management")
    print("="*60)
    
    try:
        from app.hermes_runtime import create_default_agents
        
        registry = create_default_agents(hermes.odoo_client)
        print(f"✅ Created registry: {registry}")
        print(f"   Total agents: {len(registry.agents)}")
        
        # List agents by role
        print("\n   Agents by role:")
        for agent in registry.agents.values():
            print(f"     - {agent.name} ({agent.role.value})")
        
        # Register with Hermes
        for agent_id, agent in registry.agents.items():
            hermes.register_agent(f"agent_{agent_id}", agent)
        
        print(f"\n✅ Registered {len(hermes.agents)} agents with Hermes")
        return True, registry
    except Exception as e:
        print(f"❌ Registry creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None

async def test_agent_heartbeat(registry):
    """Test 5: Agent heartbeat and status."""
    print("\n" + "="*60)
    print("TEST 5: Agent Heartbeat and Status Tracking")
    print("="*60)
    
    try:
        for agent in list(registry.agents.values())[:3]:
            heartbeat = agent.report_heartbeat()
            print(f"✅ {agent.name} heartbeat: {heartbeat}")
        
        print(f"\n✅ All agents reported successfully")
        return True
    except Exception as e:
        print(f"❌ Heartbeat failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests."""
    print("\n[*] HERMES AGENT TEST SUITE")
    print("="*60)
    
    results = []
    
    # Test 1: Import
    import_ok = await test_hermes_import()
    results.append(("Import", import_ok))
    
    if not import_ok:
        print("\n❌ Cannot proceed without imports")
        return
    
    # Test 2: Initialize
    init_ok, hermes = await test_hermes_init()
    results.append(("Initialize", init_ok))
    
    if not init_ok or not hermes:
        print("\n❌ Cannot proceed without initialization")
        return
    
    # Test 3: Start
    start_ok, hermes = await test_hermes_start(hermes)
    results.append(("Start", start_ok))
    
    if start_ok:
        # Test 4: Registry
        registry_ok, registry = await test_agent_registry(hermes)
        results.append(("Registry", registry_ok))
        
        if registry_ok and registry:
            # Test 5: Heartbeat
            heartbeat_ok = await test_agent_heartbeat(registry)
            results.append(("Heartbeat", heartbeat_ok))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)
    print(f"\n📊 Result: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n🎉 All tests passed! Hermes Agent is ready for operation.")
    else:
        print(f"\n⚠️  {total_count - passed_count} test(s) failed.")

if __name__ == "__main__":
    asyncio.run(main())
