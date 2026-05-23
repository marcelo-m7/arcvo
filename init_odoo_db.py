#!/usr/bin/env python3
"""Initialize Odoo database with required modules."""

import os
import sys
import django

# Set environment for Odoo
os.environ['ODOO_HOME'] = '/var/lib/odoo'

# Try to initialize using Odoo's service module
try:
    from odoo.service import db
    from odoo import api
    
    db_name = 'odoo'
    print(f"Initializing database '{db_name}'...")
    
    # Use Odoo's service to create and initialize the database
    db.create_database(
        'postgresql://odoo:odoo@postgresql:5432/postgres',
        db_name,
        demo=False,
        lang='en_US',
        user_password='admin'
    )
    print(f"✓ Database '{db_name}' created and initialized")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
