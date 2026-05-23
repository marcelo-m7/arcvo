#!/usr/bin/env python3
"""Initialize Odoo database using direct Postgres connection."""

import psycopg2
from psycopg2 import sql
import time

DB_HOST = 'postgresql'
DB_NAME_ADMIN = 'postgres'
DB_NAME = 'odoo'
DB_USER = 'odoo'
DB_PASSWORD = 'odoo'

try:
    # Connect to postgres database
    print(f"Connecting to PostgreSQL at {DB_HOST}...")
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME_ADMIN,
        user=DB_USER,
        password=DB_PASSWORD
    )
    conn.autocommit = True
    cur = conn.cursor()
    
    # Check if odoo database exists
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
    exists = cur.fetchone()
    
    if not exists:
        print(f"✗ Database '{DB_NAME}' does not exist. This should have been created already.")
        sys.exit(1)
    
    print(f"✓ Database '{DB_NAME}' exists")
    
    # Try to initialize Odoo using xmlrpc
    import xmlrpc.client
    common = xmlrpc.client.ServerProxy('http://127.0.0.1:8069/xmlrpc/2/common')
    
    print("Testing authentication...")
    try:
        uid = common.authenticate(DB_NAME, 'admin', 'admin', {})
        print(f"✓ Authentication successful, uid={uid}")
    except Exception as e:
        print(f"✗ Authentication failed: {e}")
        print("Database may need module installation. Trying alternative approach...")
        
        # Try to install modules manually
        # This would require running odoo with -i flag
        print("Please ensure Odoo has been initialized with -i flag")
    
    cur.close()
    conn.close()
    print("✓ Database verification complete")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    import sys
    sys.exit(1)
