# Custom Backend Layout

Configurable Odoo 19 backend layout customizations.

This addon improves the native backend app switcher drawer without modifying
Odoo core files. It is intentionally scoped to the backend webclient and does
not depend on website themes.

## Activate

1. Install `custom_backend_layout` from Odoo Apps.
2. Open **Settings > General Settings > Backend Layout**.
3. Adjust the layout options.
4. Save and reload the backend browser tab.

## Settings

- Enable or disable the custom backend layout.
- Set sidebar width.
- Toggle compact spacing.
- Show quick access links derived from the current Odoo menu.
- Limit the number of quick access links.
- Toggle app icons.
- Set an optional logo URL.
- Set accent and background colors.

Configuration is global and stored in `ir.config_parameter`.

## Evolution

Future layout customizations should reuse this addon and settings section. Keep
new behavior behind explicit settings, expose safe defaults through
`ir.http.session_info`, and scope backend styles behind the
`o_custom_backend_layout_enabled` class.
