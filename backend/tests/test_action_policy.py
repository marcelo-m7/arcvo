from app.services.action_policy import ActionPolicy


def test_action_policy_blocks_unknown_command() -> None:
    policy = ActionPolicy(["git status"])

    result = policy.run_command("rm -rf .")

    assert result.allowed is False
    assert result.returncode is None


def test_action_policy_allows_configured_command() -> None:
    policy = ActionPolicy(["git status"])

    result = policy.run_command("git status --short")

    assert result.allowed is True
    assert result.returncode == 0
