#!/usr/bin/env bash
set -euo pipefail

tools=(rg curl git uv make python3)
missing=()

for tool in "${tools[@]}"; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    missing+=("$tool")
  fi
done

if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  docker_status="ok"
else
  docker_status="missing"
fi

if ((${#missing[@]})); then
  printf 'Missing tools: %s\n' "${missing[*]}"
  printf 'Run: make install-system-tools\n'
  exit 1
fi

printf 'Required developer tools are available. Docker: %s\n' "$docker_status"
