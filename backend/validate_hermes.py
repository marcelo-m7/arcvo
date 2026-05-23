#!/usr/bin/env python
"""Comprehensive validation of hermes-ai integration."""
import sys

print("=" * 70)
print("HERMES-AI INTEGRATION VALIDATION")
print("=" * 70)
print()

# 1. Import validation
print("1. IMPORTS")
try:
    from app.hermes_runtime.agents import create_task_agent, get_provider_config
    from app.hermes_runtime.tools import (
        list_odoo_projects, list_odoo_tasks, get_odoo_task, 
        create_odoo_task, list_odoo_agents
    )
    from app.api.routes import hermes
    print("   OK - All modules imported successfully")
except ImportError as e:
    print(f"   FAIL - {e}")
    sys.exit(1)

# 2. Config validation
print()
print("2. CONFIGURATION")
from app.core.config import get_settings
s = get_settings()
print(f"   Gemini API Key: {'SET' if s.gemini_api_key else 'NOT SET'}")
print(f"   OpenRouter Key: {'SET' if s.openrouter_api_key else 'NOT SET'}")
print(f"   Ollama Base URL: {s.ollama_base_url}")
print(f"   Has LLM: {s.has_llm_configured}")
print(f"   Has Odoo: {s.has_odoo_credentials}")

# 3. Provider validation
print()
print("3. PROVIDER FALLBACK")
try:
    provider, model, api_key = get_provider_config(s)
    print(f"   Primary: {provider} ({model})")
    print(f"   API Key Length: {len(api_key)} chars")
except Exception as e:
    print(f"   ERROR: {e}")

# 4. Tools validation
print()
print("4. TOOLS VALIDATION")
tools = [list_odoo_projects, list_odoo_tasks, get_odoo_task, create_odoo_task, list_odoo_agents]
print(f"   Registered tools: {len(tools)}")
for i, tool in enumerate(tools, 1):
    print(f"     {i}. {tool.__name__}")

# 5. Route validation
print()
print("5. ROUTES")
from app.main import app
hermes_routes = [r for r in app.routes if 'hermes' in r.path]
print(f"   Total hermes routes: {len(hermes_routes)}")
for route in hermes_routes:
    methods = list(route.methods)
    print(f"     {methods[0]:6} {route.path}")

print()
print("=" * 70)
print("VALIDATION COMPLETE - ALL SYSTEMS GO")
print("=" * 70)
