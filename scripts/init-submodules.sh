#!/usr/bin/env bash
set -euo pipefail

theme_repo="odoo/external-addons/famebuilders"
git submodule update --init --depth 1 "$theme_repo"

if [[ -d "$theme_repo" ]]; then
  git -C "$theme_repo" submodule deinit -f --all >/dev/null 2>&1 || true
  git -C "$theme_repo" sparse-checkout init --cone
  git -C "$theme_repo" sparse-checkout set addons/custom_theme
  rm -rf "$theme_repo/exo" "$theme_repo/oca"
fi

printf 'Submodules initialized. Fame Builders sparse path: addons/custom_theme\n'
