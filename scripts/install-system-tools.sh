#!/usr/bin/env bash
set -euo pipefail

if [[ $EUID -eq 0 ]]; then
  sudo_cmd=()
else
  sudo_cmd=(sudo)
fi

"${sudo_cmd[@]}" apt update
"${sudo_cmd[@]}" apt install -y \
  ripgrep curl wget git make build-essential \
  ca-certificates gnupg lsb-release unzip zip

mkdir -p "$HOME/.local/bin"

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

printf 'Install complete. Ensure ~/.local/bin is in PATH.\n'
