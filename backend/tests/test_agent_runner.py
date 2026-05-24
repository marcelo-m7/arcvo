from app.services.action_policy import ActionPolicy
from app.services.agent_runner import AgentRunner


def test_agent_runner_parses_json_decision() -> None:
    data = AgentRunner._parse_decision('{"summary":"ok","status":"completed","progress":100}')

    assert data["summary"] == "ok"
    assert data["status"] == "completed"


def test_agent_runner_falls_back_for_text_decision() -> None:
    data = AgentRunner._parse_decision("plain response")

    assert data["status"] == "in_progress"
    assert data["summary"] == "plain response"


def test_runner_policy_blocks_unlisted_command() -> None:
    policy = ActionPolicy(["git status"])

    result = policy.run_command("make deploy")

    assert result.allowed is False
