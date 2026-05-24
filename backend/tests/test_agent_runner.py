from app.integrations.ollama import OllamaClient
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


def test_ollama_client_no_auth_headers() -> None:
    client = OllamaClient(base_url="https://ollama.example.com", model="qwen")
    assert client._headers() == {}


def test_ollama_client_with_password_sends_bearer() -> None:
    client = OllamaClient(
        base_url="https://ollama.example.com", model="qwen", password="secret"
    )
    assert client._headers() == {"Authorization": "Bearer secret"}


def test_agent_runner_prompt_contains_agent_and_task() -> None:
    agent = {"name": "Backend Operator", "role": "backend", "description": "Runs APIs"}
    task = {"name": "Fix health endpoint", "description": "500 on /health"}
    assignment = {"notes": "urgent"}
    prompt = AgentRunner._build_prompt(agent, task, assignment)

    assert "Backend Operator" in prompt
    assert "Fix health endpoint" in prompt
    assert "urgent" in prompt
