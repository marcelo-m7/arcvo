SHELL := /bin/bash
PATH := $(HOME)/.local/bin:$(PATH)
export UV_PROJECT_ENVIRONMENT := .venv-linux
export UV_LINK_MODE := copy

.PHONY: install backend lint format test odoo-health validate-addons all tools-check install-system-tools

install: tools-check
	cd backend && uv sync

backend:
	cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

lint:
	cd backend && uv run --no-sync ruff check .

format:
	cd backend && uv run --no-sync ruff format .

test:
	cd backend && PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run --no-sync pytest --capture=no

odoo-health:
	cd backend && uv run python -m scripts.odoo_health

validate-addons:
	cd backend && uv run --no-sync python -m scripts.validate_addons

all: lint test validate-addons

tools-check:
	@bash scripts/check-tools.sh

install-system-tools:
	@bash scripts/install-system-tools.sh
