# custom_theme

FAME Builders custom Odoo Website theme addon.

## Purpose

`custom_theme` provides branded theme behavior and visual assets for a corporate engineering website style.

Key contributions:
- Theme metadata and configurator snippet defaults.
- Website asset customizations (SCSS, images, editor JS).
- Theme data templates and view resources.
- Translation files for multiple languages.

## Module Metadata

- Name: `FAME Builders Theme`
- Version: `2.1.0`
- Category: `Theme/Corporate`
- License: `LGPL-3`
- Depends: `website`
- Author: `Corvanis / FAME Builders`

## Loaded Data

The manifest currently loads:
- `data/generate_primary_template.xml`
- `data/ir_asset.xml`
- `views/image_content.xml`

Additional snippet and page template files are present under `views/` but are not currently enabled in the manifest `data` list.

## Post-Copy Theme Behavior

The model extension in `models/custom_theme.py` inherits `theme.utils` and enables:
- `website.template_header_default`
- `website.template_footer_contact`

This runs in `_custom_theme_post_copy` when the theme is copied/applied.

## Assets

Editor assets include:
- `static/src/js/tour.js` (loaded in `website.assets_editor`)

Style and media resources live under:
- `static/src/scss/`
- `static/src/img/`

## Installation

1. Ensure this addon is in Odoo's addons path.
2. Update the Apps list (developer mode).
3. Install `custom_theme` from Apps.
4. Open Website and apply/configure the theme.

## Development Notes

- Snippet XML files can be enabled by adding them to `__manifest__.py` under `data`.
- Keep translation updates in `i18n/` aligned with view/template changes.
- Rebuild/reload website assets after SCSS or JS updates.

## License

Licensed under LGPL-3. See `LICENSE`.
