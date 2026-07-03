import ast
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
ADDONS_DIR = ROOT / "odoo" / "addons"
ODOO_DOCKERFILE = ROOT / "odoo" / "Dockerfile"
TEMPLATE_OWNED_ADDONS = {"custom_base", "custom_backend_layout", "custom_theme"}


def _load_manifest(path: Path) -> dict[str, Any]:
    try:
        data = ast.literal_eval(path.read_text(encoding="utf-8"))
    except (SyntaxError, ValueError) as exc:
        raise SystemExit(f"Invalid manifest syntax: {path}") from exc

    if not isinstance(data, dict):
        raise SystemExit(f"Manifest must be a dictionary: {path}")
    return data


def _validate_xml(path: Path) -> None:
    try:
        ET.parse(path)
    except ET.ParseError as exc:
        raise SystemExit(f"Invalid XML in {path}: {exc}") from exc


def _validate_addon(
    addon_dir: Path,
    require_base: bool = False,
    require_installable_key: bool = False,
    require_lgpl3: bool = False,
) -> None:
    manifest_path = addon_dir / "__manifest__.py"
    init_path = addon_dir / "__init__.py"
    if not manifest_path.exists():
        raise SystemExit(f"Missing manifest: {manifest_path}")
    if not init_path.exists():
        raise SystemExit(f"Missing init file: {init_path}")

    manifest = _load_manifest(manifest_path)
    required_keys = ["name", "summary", "depends", "license"]
    if require_installable_key:
        required_keys.append("installable")

    for key in required_keys:
        if key not in manifest:
            raise SystemExit(f"Manifest {manifest_path} is missing {key!r}")

    if require_lgpl3 and manifest["license"] != "LGPL-3":
        raise SystemExit(f"Manifest {manifest_path} must use LGPL-3")
    if require_base and "base" not in manifest["depends"]:
        raise SystemExit(f"Manifest {manifest_path} must depend on base")

    for xml_path in addon_dir.rglob("*.xml"):
        _validate_xml(xml_path)


def _validate_dockerfile() -> None:
    text = ODOO_DOCKERFILE.read_text(encoding="utf-8")
    if "FROM odoo:19" not in text:
        raise SystemExit("Odoo Dockerfile must remain based on odoo:19")
    if "/mnt/extra-addons" not in text:
        raise SystemExit("Odoo Dockerfile must copy addons to /mnt/extra-addons")


def main() -> None:
    if not ADDONS_DIR.exists():
        raise SystemExit(f"Missing addons directory: {ADDONS_DIR}")

    addon_dirs = sorted(path for path in ADDONS_DIR.iterdir() if path.is_dir())
    if not addon_dirs:
        raise SystemExit("No Odoo addons found")

    for addon_dir in addon_dirs:
        # Keep strict checks for template-owned addons only.
        is_template_owned = addon_dir.name in TEMPLATE_OWNED_ADDONS
        is_template_starter = addon_dir.name == "custom_base"
        _validate_addon(
            addon_dir,
            require_base=is_template_starter,
            require_installable_key=is_template_starter,
            require_lgpl3=is_template_owned,
        )
    _validate_dockerfile()

    print(f"Validated {len(addon_dirs)} local addon(s).")


if __name__ == "__main__":
    main()
