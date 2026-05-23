SHELL := /bin/bash
PATH := $(HOME)/.local/bin:$(PATH)

.PHONY: install dev frontend backend lint format test odoo-health docker-up docker-down tools-check install-system-tools

install: tools-check
	cd backend && uv sync
	pnpm install

dev:
	$(MAKE) -j2 backend frontend

frontend:
	pnpm --dir frontend dev

backend:
	cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

lint:
	cd backend && uv run ruff check .
	pnpm --dir frontend lint

format:
	cd backend && uv run ruff format .
	pnpm --dir frontend format

test:
	cd backend && PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest --capture=no
	pnpm --dir frontend typecheck
	pnpm --dir frontend build

odoo-health:
	cd backend && uv run python -m scripts.odoo_health

import-supabase-youtube:
	cd backend && uv run python -m scripts.import_supabase_youtube --fetch-supabase --export ../.data/supabase_youtube.json --execute

dry-run-supabase-youtube:
	cd backend && uv run python -m scripts.import_supabase_youtube --fetch-supabase --export ../.data/supabase_youtube.json

docker-up:
	docker compose up -d

docker-down:
	docker compose down

tools-check:
	@bash scripts/check-tools.sh

install-system-tools:
	@bash scripts/install-system-tools.sh
