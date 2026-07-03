import re

from odoo import fields, models
from odoo.tools.misc import str2bool


DEFAULT_LAYOUT_CONFIG = {
    "enabled": True,
    "sidebar_width": 360,
    "compact_mode": False,
    "show_quick_access": True,
    "quick_access_limit": 6,
    "show_app_icons": True,
    "logo_url": "",
    "accent_color": "#7c3aed",
    "background_color": "#111827",
}

COLOR_PATTERN = re.compile(r"^[#a-zA-Z0-9(),.%\s-]{1,64}$")


def _as_bool(value, default=False):
    if value in (None, ""):
        return default
    return str2bool(str(value), default)


def _as_int(value, default, minimum, maximum):
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = default
    return min(max(number, minimum), maximum)


def _as_color(value, default):
    if not value:
        return default
    value = str(value).strip()
    if COLOR_PATTERN.fullmatch(value):
        return value
    return default


def _as_url(value):
    if not value:
        return ""
    value = str(value).strip()
    if len(value) > 512:
        return ""
    if value.startswith(("/", "http://", "https://")):
        return value
    return ""


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    custom_backend_layout_enabled = fields.Boolean(
        string="Enable backend layout",
        config_parameter="custom_backend_layout.enabled",
        default=DEFAULT_LAYOUT_CONFIG["enabled"],
    )
    custom_backend_layout_sidebar_width = fields.Integer(
        string="Sidebar width",
        config_parameter="custom_backend_layout.sidebar_width",
        default=DEFAULT_LAYOUT_CONFIG["sidebar_width"],
    )
    custom_backend_layout_compact_mode = fields.Boolean(
        string="Compact mode",
        config_parameter="custom_backend_layout.compact_mode",
        default=DEFAULT_LAYOUT_CONFIG["compact_mode"],
    )
    custom_backend_layout_show_quick_access = fields.Boolean(
        string="Show quick access",
        config_parameter="custom_backend_layout.show_quick_access",
        default=DEFAULT_LAYOUT_CONFIG["show_quick_access"],
    )
    custom_backend_layout_quick_access_limit = fields.Integer(
        string="Quick access limit",
        config_parameter="custom_backend_layout.quick_access_limit",
        default=DEFAULT_LAYOUT_CONFIG["quick_access_limit"],
    )
    custom_backend_layout_show_app_icons = fields.Boolean(
        string="Show app icons",
        config_parameter="custom_backend_layout.show_app_icons",
        default=DEFAULT_LAYOUT_CONFIG["show_app_icons"],
    )
    custom_backend_layout_logo_url = fields.Char(
        string="Logo URL",
        config_parameter="custom_backend_layout.logo_url",
        default=DEFAULT_LAYOUT_CONFIG["logo_url"],
    )
    custom_backend_layout_accent_color = fields.Char(
        string="Accent color",
        config_parameter="custom_backend_layout.accent_color",
        default=DEFAULT_LAYOUT_CONFIG["accent_color"],
    )
    custom_backend_layout_background_color = fields.Char(
        string="Background color",
        config_parameter="custom_backend_layout.background_color",
        default=DEFAULT_LAYOUT_CONFIG["background_color"],
    )

    def get_custom_backend_layout_config(self):
        params = self.env["ir.config_parameter"].sudo()

        return {
            "enabled": _as_bool(
                params.get_param(
                    "custom_backend_layout.enabled",
                    default=DEFAULT_LAYOUT_CONFIG["enabled"],
                ),
                DEFAULT_LAYOUT_CONFIG["enabled"],
            ),
            "sidebarWidth": _as_int(
                params.get_param(
                    "custom_backend_layout.sidebar_width",
                    default=DEFAULT_LAYOUT_CONFIG["sidebar_width"],
                ),
                DEFAULT_LAYOUT_CONFIG["sidebar_width"],
                280,
                520,
            ),
            "compactMode": _as_bool(
                params.get_param(
                    "custom_backend_layout.compact_mode",
                    default=DEFAULT_LAYOUT_CONFIG["compact_mode"],
                ),
                DEFAULT_LAYOUT_CONFIG["compact_mode"],
            ),
            "showQuickAccess": _as_bool(
                params.get_param(
                    "custom_backend_layout.show_quick_access",
                    default=DEFAULT_LAYOUT_CONFIG["show_quick_access"],
                ),
                DEFAULT_LAYOUT_CONFIG["show_quick_access"],
            ),
            "quickAccessLimit": _as_int(
                params.get_param(
                    "custom_backend_layout.quick_access_limit",
                    default=DEFAULT_LAYOUT_CONFIG["quick_access_limit"],
                ),
                DEFAULT_LAYOUT_CONFIG["quick_access_limit"],
                0,
                12,
            ),
            "showAppIcons": _as_bool(
                params.get_param(
                    "custom_backend_layout.show_app_icons",
                    default=DEFAULT_LAYOUT_CONFIG["show_app_icons"],
                ),
                DEFAULT_LAYOUT_CONFIG["show_app_icons"],
            ),
            "logoUrl": _as_url(
                params.get_param(
                    "custom_backend_layout.logo_url",
                    default=DEFAULT_LAYOUT_CONFIG["logo_url"],
                )
            ),
            "accentColor": _as_color(
                params.get_param(
                    "custom_backend_layout.accent_color",
                    default=DEFAULT_LAYOUT_CONFIG["accent_color"],
                ),
                DEFAULT_LAYOUT_CONFIG["accent_color"],
            ),
            "backgroundColor": _as_color(
                params.get_param(
                    "custom_backend_layout.background_color",
                    default=DEFAULT_LAYOUT_CONFIG["background_color"],
                ),
                DEFAULT_LAYOUT_CONFIG["background_color"],
            ),
        }
