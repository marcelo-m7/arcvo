#!/usr/bin/env python3
"""Test if agent_registry addon is available in Odoo."""

import xmlrpc.client
import sys

url = 'http://127.0.0.1:8069'
db = 'odoo'
username = 'admin'
password = 'admin'

try:
    # Authenticate
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
    uid = common.authenticate(db, username, password, {})
    print(f"✓ Authenticated as UID: {uid}")
    
    # Check addon
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
    
    # Search for agent_registry addon
    addons = models.execute_kw(
        db, uid, password,
        'ir.module.module',
        'search_read',
        [['name', '=', 'agent_registry']],
        {'fields': ['name', 'state', 'installable']}
    )
    
    if addons:
        addon = addons[0]
        print(f"\n✓ Addon found: {addon['name']}")
        print(f"  State: {addon['state']}")
        print(f"  Installable: {addon.get('installable', 'N/A')}")
        
        if addon['state'] == 'uninstalled':
            print("\n→ Installing addon...")
            # Button click to install
            models.execute_kw(db, uid, password, 'ir.module.module', 'button_immediate_install', [addon['id']])
            print("✓ Install command sent")
            
            # Check state again
            import time
            time.sleep(2)
            addon = models.execute_kw(db, uid, password, 'ir.module.module', 'read', [addon['id']], {'fields': ['state']})
            print(f"  New state: {addon[0]['state']}")
            
    else:
        print("\n✗ Addon 'agent_registry' NOT found")
        print("\nSearching for similar addons...")
        all_addons = models.execute_kw(
            db, uid, password,
            'ir.module.module',
            'search_read',
            [['name', 'ilike', '%agent%']],
            {'fields': ['name', 'state']}
        )
        if all_addons:
            print(f"Found {len(all_addons)} addon(s) with 'agent' in name:")
            for a in all_addons:
                print(f"  - {a['name']}: {a['state']}")
        else:
            print("  No addons with 'agent' found")
            
except xmlrpc.client.Fault as e:
    print(f"✗ Odoo XML-RPC Error: {e.faultCode}: {e.faultString}")
    sys.exit(1)
except Exception as e:
    print(f"✗ Error: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
