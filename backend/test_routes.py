#!/usr/bin/env python3
"""List all registered routes in the FastAPI app."""

from app.main import app

print("Routes registered:")
for route in app.routes:
    print(f"  {route.path} - {route.methods if hasattr(route, 'methods') else 'N/A'}")
