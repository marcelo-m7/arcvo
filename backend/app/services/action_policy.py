import subprocess
from dataclasses import dataclass
from pathlib import Path

from app.core.config import settings

ROOT_DIR = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class CommandResult:
    command: str
    allowed: bool
    returncode: int | None = None
    stdout: str = ""
    stderr: str = ""
    reason: str | None = None


class ActionPolicy:
    def __init__(self, allowed_commands: list[str] | None = None) -> None:
        self.allowed_commands = allowed_commands or settings.allowed_agent_commands

    def is_allowed(self, command: str) -> bool:
        normalized = " ".join(command.strip().split())
        return any(
            normalized == allowed or normalized.startswith(f"{allowed} ")
            for allowed in self.allowed_commands
        )

    def run_command(self, command: str) -> CommandResult:
        normalized = " ".join(command.strip().split())
        if not self.is_allowed(normalized):
            return CommandResult(
                command=normalized,
                allowed=False,
                reason="Command is not in the Arcvo agent allowlist.",
            )
        completed = subprocess.run(
            normalized.split(),
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        return CommandResult(
            command=normalized,
            allowed=True,
            returncode=completed.returncode,
            stdout=completed.stdout[-4000:],
            stderr=completed.stderr[-4000:],
        )
