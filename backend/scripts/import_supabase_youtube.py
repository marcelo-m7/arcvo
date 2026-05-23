import argparse
import json
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.integrations.odoo.client import OdooClient, OdooCredentials
from app.integrations.supabase import SupabaseArchiveClient
from app.services.supabase_importer import SupabaseOdooImporter


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import Supabase YouTube archive into Odoo.")
    parser.add_argument("--input", help="JSON file exported from Supabase MCP SQL.")
    parser.add_argument(
        "--fetch-supabase",
        action="store_true",
        help="Fetch rows from Supabase REST.",
    )
    parser.add_argument("--export", help="Write fetched Supabase rows to this JSON file.")
    parser.add_argument("--execute", action="store_true", help="Write records to Odoo.")
    parser.add_argument(
        "--no-update-existing",
        action="store_true",
        help="Skip existing Odoo videos instead of updating metadata.",
    )
    parser.add_argument("--draft", action="store_true", help="Create/update as unpublished draft.")
    return parser.parse_args()


def load_rows(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text())
    if isinstance(data, dict) and isinstance(data.get("rows"), list):
        return data["rows"]
    if isinstance(data, list):
        return data
    raise ValueError("Input must be a JSON array or an object with a rows array")


def main() -> None:
    args = parse_args()
    if args.fetch_supabase:
        if not settings.supabase_publishable_key:
            raise ValueError("SUPABASE_PUBLISHABLE_KEY is required for --fetch-supabase")
        rows = SupabaseArchiveClient(
            settings.supabase_url,
            settings.supabase_publishable_key,
        ).fetch_youtube_archive()
        if args.export:
            export_path = Path(args.export)
            export_path.parent.mkdir(parents=True, exist_ok=True)
            export_path.write_text(json.dumps({"rows": rows}, indent=2, ensure_ascii=False))
    elif args.input:
        rows = load_rows(Path(args.input))
    else:
        raise ValueError("Provide --input or --fetch-supabase")
    credentials = OdooCredentials(
        url=settings.odoo_url,
        database=settings.odoo_db,
        username=settings.odoo_user,
        api_key=settings.odoo_api_key,
        allow_self_signed_ssl=settings.odoo_allow_self_signed_ssl,
    )
    importer = SupabaseOdooImporter(
        OdooClient(credentials),
        publish=not args.draft,
        update_existing=not args.no_update_existing,
    )
    stats = importer.import_rows(rows, dry_run=not args.execute)
    print(json.dumps(stats.as_dict(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
