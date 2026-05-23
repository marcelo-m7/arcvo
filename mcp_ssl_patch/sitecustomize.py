"""Local TLS workaround for the Odoo MCP process.

This is intentionally opt-in. It exists because the current Odoo endpoint
serves Traefik's self-signed default certificate, which prevents Python's
XML-RPC client from connecting.
"""

import os
import ssl


if os.getenv("ODOO_ALLOW_SELF_SIGNED_SSL", "").strip().lower() in {"1", "true", "yes"}:
    ssl._create_default_https_context = ssl._create_unverified_context
