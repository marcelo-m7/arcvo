import ast
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ADDON = ROOT / "odoo" / "addons" / "arcvo_agents"

REQUIRED_FILES = [
    "__init__.py",
    "__manifest__.py",
    "models/__init__.py",
    "models/agent_orchestration.py",
    "models/capability.py",
    "models/assignment.py",
    "models/audit_log.py",
    "models/project_task.py",
    "security/ir.model.access.csv",
    "views/agent_views.xml",
    "views/capability_views.xml",
    "views/assignment_views.xml",
    "views/audit_log_views.xml",
    "views/project_task_views.xml",
    "data/arcvo_agent_data.xml",
]

REQUIRED_MODELS = {
    "arcvo.agent.capability",
    "arcvo.agent.assignment",
    "arcvo.agent.audit.log",
    "hr.employee",
}

FORBIDDEN_TEXT = {
    "agent_registry",
    "autonomous_agents",
    '"agent.agent"',
    "'agent.agent'",
    '_name = "arcvo.agent"',
    "_name = 'arcvo.agent'",
    'model="arcvo.agent"',
    'res_model">arcvo.agent<',
    "model_arcvo_agent,",
    "<tree",
    "</tree>",
    "view_mode\">tree",
    "attrs=",
    "states=",
    "numbercall",
    "doall",
}


TEXT_SUFFIXES = {".csv", ".py", ".xml"}


def main() -> None:
    missing = [path for path in REQUIRED_FILES if not (ADDON / path).exists()]
    if missing:
        raise SystemExit(f"Missing arcvo_agents files: {', '.join(missing)}")

    manifest = ast.literal_eval((ADDON / "__manifest__.py").read_text(encoding="utf-8"))
    if manifest["name"] != "Arcvo Agents":
        raise SystemExit("Unexpected addon name in manifest.")
    depends = manifest.get("depends", [])
    if "project" not in depends:
        raise SystemExit("arcvo_agents must depend on project.")
    if "website_slides" not in depends:
        raise SystemExit("arcvo_agents must depend on website_slides.")

    all_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in ADDON.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix in TEXT_SUFFIXES
    )
    for model in REQUIRED_MODELS:
        if model not in all_text:
            raise SystemExit(f"Required model not found in addon source: {model}")
    for forbidden in FORBIDDEN_TEXT:
        if forbidden in all_text:
            raise SystemExit(f"Forbidden legacy reference found: {forbidden}")
    if 'model="res.groups"' in all_text and "category_id" in all_text:
        raise SystemExit("Odoo 19 res.groups records must not use category_id.")

    with (ADDON / "security" / "ir.model.access.csv").open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) < 4:
        raise SystemExit("Expected access rules for all arcvo agent models.")

    print("arcvo_agents addon structure is valid.")


if __name__ == "__main__":
    main()
