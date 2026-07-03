# -*- coding: utf-8 -*-
{
    "name": "Google Drive Connector",
    "version": "19.0.1.0.0",
    "category": "Document Management",
    "summary": "Connect Odoo to Google Drive: per-record folders, push attachments as "
               "shareable links, optional one-way sync. OAuth & Service Account.",
    "description": """
Google Drive Connector
=======================

A lightweight, focused bridge between Odoo attachments and Google Drive.

* Connect one or more Google Drive accounts (OAuth user consent or Service Account).
* Each business record gets its own Drive folder, laid out as Root / Model / Record.
* Push attachments to Drive in one click; the file becomes a shareable link on the record.
* Optionally offload the binary to free Odoo storage, or keep a local copy.
* Optional scheduled one-way push (Odoo -> Drive) per configured model.
* Shared (Team) Drive support.

Independent implementation. No third-party framework required.
    """,
    "author": "OAKLAND - odooERP.ae",
    "website": "https://odooerp.ae/",
    "support": "apps@odooerp.ae",
    "license": "OPL-1",
    'price': 0.00,
    'currency': 'EUR',
    "depends": ["base", "mail", "web"],
    "external_dependencies": {
        "python": ["googleapiclient", "google_auth_oauthlib", "google.auth"],
    },
    "data": [
        "security/gdrive_security.xml",
        "security/ir.model.access.csv",
        "data/gdrive_cron.xml",
        "views/gdrive_connection_views.xml",
        "views/gdrive_mapping_views.xml",
        "views/gdrive_log_views.xml",
        "views/ir_attachment_views.xml",
        "views/res_config_settings_views.xml",
        "wizards/gdrive_push_wizard_views.xml",
        "views/gdrive_menus.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "oe_google_drive_connector/static/src/message_gdrive_action.js",
        ],
    },
    "images": ["static/description/Banner.gif"],
    "application": True,
    "installable": True,
    "auto_install": False,
}
