#!/usr/bin/env python3
"""Create Odoo database through HTTP interface."""

import requests
import json
import time

BASE_URL = 'http://127.0.0.1:8069'
headers = {'Content-Type': 'application/x-www-form-urlencoded'}

# Try to create database via web endpoint
try:
    print("Attempting to create Odoo database...")
    
    # First attempt: try /web/database/create endpoint
    session = requests.Session()
    
    # Get CSRF token from database selector
    resp = session.get(f'{BASE_URL}/web/database/selector')
    print(f"✓ Database selector accessible: {resp.status_code}")
    
    # Try to create database
    data = {
        'master_pwd': 'admin',
        'name': 'odoo',
        'login': 'admin',
        'password': 'admin',
        'lang': 'en_US',
        'country_code': 'US'
    }
    
    resp = session.post(f'{BASE_URL}/web/database/create', data=data)
    print(f"Database create response: {resp.status_code}")
    print(f"Response text (first 200 chars): {resp.text[:200]}")
    
    time.sleep(5)
    
    # Check if database was created
    print("\nChecking database status...")
    resp = session.get(f'{BASE_URL}/')
    print(f"Home page status: {resp.status_code}")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
