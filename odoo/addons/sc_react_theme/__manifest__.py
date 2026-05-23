# Copyright 2026 Shachain
# License OPL-1 (Odoo Proprietary License v1.0)
{
    "name": "SC React Theme",
    "version": "19.0.2.0.0",
    "category": "Theme/Backend",
    "summary": "Shadcn/zinc design theme — unified React and native Odoo styling",
    "description": "Shadcn zinc design tokens applied to Odoo SCSS variables. Unifies React and native styling.",
    "author": "Shachain",
    "website": "https://shachain.dev",
    "support": "business@shachain.dev",
    "license": "OPL-1",
    "depends": ["web"],
    "images": [
        "static/description/banner.png",
        "static/description/icon.png",
    ],
    "live_test_url": "https://demo.shachain.dev",
    "assets": {
        "web._assets_primary_variables": [
            (
                "before",
                "web/static/src/scss/primary_variables.scss",
                "sc_react_theme/static/src/scss/primary_variables.scss",
            ),
            (
                "before",
                "web/static/src/webclient/navbar/navbar.variables.scss",
                "sc_react_theme/static/src/webclient/navbar/navbar.variables.scss",
            ),
        ],
    },
    "installable": True,
    "auto_install": False,
    "application": False,
}
