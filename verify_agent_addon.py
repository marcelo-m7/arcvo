#!/usr/bin/env python3
"""Simple test to verify agent_registry addon is installed."""

import xmlrpc.client

url = 'http://127.0.0.1:8069'
db = 'odoo'
username = 'admin'
password = 'admin'

try:
    # Authenticate
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
    uid = common.authenticate(db, username, password, {})
    print(f"✓ Authenticated as UID: {uid}")
    
    # Check addon state
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
    
    # Search for agent_registry module
    addon_results = models.execute_kw(
        db, uid, password,
        'ir.module.module',
        'search',
        [['name', '=', 'agent_registry']],
        {}
    )
    
    if addon_results:
        addon_id = addon_results[0]
        addon_data = models.execute_kw(
            db, uid, password,
            'ir.module.module',
            'read',
            [addon_id],
            {'fields': ['name', 'state']}
        )
        addon = addon_data[0]
        print(f"✓ Agent Registry addon found: {addon['name']}")
        print(f"  State: {addon['state']}")
        
        if addon['state'] == 'installed':
            print("\n✓ SUCCESS: agent_registry addon is INSTALLED")
            
            # Try to search for agent records
            print("\n→ Checking agent model...")
            agent_count = models.execute_kw(
                db, uid, password,
                'agent.agent',
                'search_count',
                []
            )
            print(f"✓ Found {agent_count} agents in database")
        else:
            print(f"\n✗ Addon is not installed, state is: {addon['state']}")
    else:
        print("✗ Agent Registry addon NOT found")
        
except xmlrpc.client.Fault as e:
    print(f"✗ Odoo XML-RPC Error: {e.faultCode}")
    print(f"  Message: {e.faultString}")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
