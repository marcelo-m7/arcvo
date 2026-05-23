#!/usr/bin/env bash
set -euo pipefail

if [[ $EUID -eq 0 ]]; then
  sudo_cmd=()
else
  sudo_cmd=(sudo)
fi

"${sudo_cmd[@]}" apt update
"${sudo_cmd[@]}" apt install -y \
  ripgrep fd-find fzf bat jq tree htop curl wget git make build-essential \
  ca-certificates gnupg lsb-release unzip zip

mkdir -p "$HOME/.local/bin"
if command -v fdfind >/dev/null 2>&1 && ! command -v fd >/dev/null 2>&1; then
  ln -sf "$(command -v fdfind)" "$HOME/.local/bin/fd"
fi
if command -v batcat >/dev/null 2>&1 && ! command -v bat >/dev/null 2>&1; then
  ln -sf "$(command -v batcat)" "$HOME/.local/bin/bat"
fi

if ! command -v docker >/dev/null 2>&1; then
  "${sudo_cmd[@]}" install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg |
    "${sudo_cmd[@]}" gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  "${sudo_cmd[@]}" chmod a+r /etc/apt/keyrings/docker.gpg
  . /etc/os-release
  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu ${VERSION_CODENAME} stable" |
    "${sudo_cmd[@]}" tee /etc/apt/sources.list.d/docker.list >/dev/null
  "${sudo_cmd[@]}" apt update
  "${sudo_cmd[@]}" apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
fi

if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi

if ! command -v pnpm >/dev/null 2>&1; then
  npm install --prefix "$HOME/.local" pnpm@10
  ln -sf "$HOME/.local/node_modules/pnpm/bin/pnpm.cjs" "$HOME/.local/bin/pnpm"
  ln -sf "$HOME/.local/node_modules/pnpm/bin/pnpx.cjs" "$HOME/.local/bin/pnpx"
fi

printf 'Install complete. Ensure ~/.local/bin is in PATH.\n'
