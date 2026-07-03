{
    "name": "Custom Backend Layout",
    "summary": "Configurable backend layout customizations for Odoo.",
    "version": "19.0.1.0.0",
    "category": "Tools",
    "author": "Template Maintainers",
    "license": "LGPL-3",
    "depends": ["base", "web", "base_setup"],
    "data": [
        "views/res_config_settings_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "custom_backend_layout/static/src/js/sidebar_patch.js",
            "custom_backend_layout/static/src/xml/sidebar.xml",
            "custom_backend_layout/static/src/scss/sidebar.scss",
        ],
    },
    "installable": True,
    "application": False,
}
