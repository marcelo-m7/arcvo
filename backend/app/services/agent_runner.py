import json
from typing import Any

from app.core.config import settings
from app.integrations.odoo.client import OdooClient, OdooCredentials
from app.integrations.ollama import OllamaClient, OllamaError
from app.schemas.agents import AgentChatResponse, AgentExecution
from app.services.action_policy import ActionPolicy
from app.services.agent_service import AGENT_MODEL, ASSIGNMENT_MODEL, AUDIT_MODEL, TASK_MODEL


class AgentRunner:
    def __init__(
        self,
        client: OdooClient,
        ollama: OllamaClient,
        policy: ActionPolicy | None = None,
    ) -> None:
        self.client = client
        self.ollama = ollama
        self.policy = policy or ActionPolicy()

    async def run_agent(self, agent_id: int, limit: int = 1) -> list[AgentExecution]:
        assignments = self.client.search_read(
            ASSIGNMENT_MODEL,
            domain=[["agent_id", "=", agent_id], ["status", "in", ["assigned", "in_progress"]]],
            fields=["id", "agent_id", "task_id", "status", "notes"],
            limit=limit,
        )
        return [await self._run_assignment(assignment) for assignment in assignments]

    async def run_pending(self, limit: int = 5) -> list[AgentExecution]:
        assignments = self.client.search_read(
            ASSIGNMENT_MODEL,
            domain=[["status", "in", ["assigned", "in_progress"]]],
            fields=["id", "agent_id", "task_id", "status", "notes"],
            limit=limit,
        )
        executions = []
        for assignment in assignments:
            executions.append(await self._run_assignment(assignment))
        return executions

    def list_executions(self, limit: int = 50) -> list[dict[str, Any]]:
        records = self.client.search_read(
            AUDIT_MODEL,
            domain=[["action", "in", ["progress", "completed", "failed", "blocked"]]],
            fields=[
                "id", "agent_id", "task_id", "assignment_id", "action", "message", "created_at",
            ],
            limit=limit,
        )
        return [{**r, "payload": None} for r in records]

    async def chat(self, agent_id: int, message: str) -> AgentChatResponse:
        agents = self.client.search_read(
            AGENT_MODEL,
            domain=[["id", "=", agent_id]],
            fields=["id", "name", "role", "description"],
            limit=1,
        )
        if not agents:
            raise ValueError(f"Agent {agent_id} not found")
        agent = agents[0]
        prompt = (
            f"Voce e {agent['name']}, um agente Arcvo com o papel de {agent['role']}. "
            f"{agent.get('description') or ''} "
            "Responda em portugues, de forma direta e profissional, como um colaborador digital. "
            "Nao use JSON. Responda naturalmente ao usuario.\n\n"
            f"Usuario: {message}"
        )
        try:
            reply = await self.ollama.generate(prompt)
            # Strip JSON if the model accidentally returns it
            stripped = reply.strip()
            if stripped.startswith("{"):
                import json as _json  # noqa: PLC0415

                try:
                    data = _json.loads(stripped)
                    reply = data.get("summary") or data.get("reply") or stripped
                except Exception:
                    pass
        except OllamaError as exc:
            reply = f"[Ollama indisponivel: {exc}]"
        return AgentChatResponse(
            agent_id=agent_id,
            agent_name=agent["name"],
            role=agent["role"],
            reply=reply,
        )

    async def _run_assignment(self, assignment: dict[str, Any]) -> AgentExecution:
        assignment_id = assignment["id"]
        agent_id = self._many2one_id(assignment["agent_id"])
        task_id = self._many2one_id(assignment["task_id"])
        agent = self.client.search_read(
            AGENT_MODEL,
            domain=[["id", "=", agent_id]],
            fields=["id", "name", "role", "description", "capability_ids"],
            limit=1,
        )[0]
        task = self.client.search_read(
            TASK_MODEL,
            domain=[["id", "=", task_id]],
            fields=["id", "name", "description", "stage_id", "project_id"],
            limit=1,
        )[0]
        prompt = self._build_prompt(agent, task, assignment)
        try:
            ollama_text = await self.ollama.generate(prompt)
            decision = self._parse_decision(ollama_text)
        except OllamaError as exc:
            decision = {
                "summary": f"Ollama unavailable: {exc}",
                "status": "blocked",
                "progress": 0,
                "command": "",
            }

        command = str(decision.get("command") or "").strip()
        command_result = self.policy.run_command(command) if command else None
        status = str(decision.get("status") or "in_progress")
        if status not in {"assigned", "in_progress", "blocked", "completed", "failed"}:
            status = "in_progress"
        progress = int(decision.get("progress") or (100 if status == "completed" else 25))
        progress = max(0, min(100, progress))
        message = str(decision.get("summary") or "Agent execution completed.")

        payload = {
            "ollama_model": settings.ollama_model,
            "command": command,
            "command_result": command_result.__dict__ if command_result else None,
        }
        self._apply_assignment_update(
            assignment_id=assignment_id,
            status=status,
            progress=progress,
            message=message,
            payload=payload,
        )
        return AgentExecution(
            assignment_id=assignment_id,
            agent_id=agent_id,
            task_id=task_id,
            status=status,
            progress=progress,
            summary=message,
            command=command or None,
            command_allowed=command_result.allowed if command_result else None,
        )

    @staticmethod
    def _many2one_id(value: Any) -> int:
        if isinstance(value, list):
            return int(value[0])
        return int(value)

    @staticmethod
    def _build_prompt(
        agent: dict[str, Any],
        task: dict[str, Any],
        assignment: dict[str, Any],
    ) -> str:
        return (
            "Voce e um funcionario digital do Arcvo operando com Odoo como delegador. "
            "Responda somente JSON valido com as chaves summary, status, progress e command. "
            "Use command vazio salvo se uma acao de diagnostico segura for necessaria. "
            "Status permitido: in_progress, blocked, completed, failed. "
            f"Agente: {agent.get('name')} ({agent.get('role')}). "
            f"Tarefa: {task.get('name')}. Descricao: {task.get('description') or ''}. "
            f"Notas da atribuicao: {assignment.get('notes') or ''}."
        )

    @staticmethod
    def _parse_decision(text: str) -> dict[str, Any]:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            try:
                data = json.loads(text[start : end + 1])
                if isinstance(data, dict):
                    return data
            except json.JSONDecodeError:
                pass
        return {"summary": text[:1000], "status": "in_progress", "progress": 25, "command": ""}

    def _apply_assignment_update(
        self,
        assignment_id: int,
        status: str,
        progress: int,
        message: str,
        payload: dict[str, Any],
    ) -> None:
        self.client.execute_kw(
            ASSIGNMENT_MODEL,
            "action_apply_progress",
            [[assignment_id]],
            {
                "status": status,
                "progress": progress,
                "result": message,
                "error_message": message if status in {"failed", "blocked"} else "",
                "payload": payload,
            },
        )


def get_agent_runner() -> AgentRunner:
    credentials = OdooCredentials(
        url=settings.odoo_url,
        database=settings.odoo_db,
        username=settings.odoo_user,
        api_key=settings.odoo_api_key,
        allow_self_signed_ssl=settings.odoo_allow_self_signed_ssl,
    )
    ollama = OllamaClient(
        base_url=settings.ollama_url,
        model=settings.ollama_model,
        timeout=settings.ollama_timeout_seconds,
        password=settings.ollama_ui_senha,
    )
    return AgentRunner(OdooClient(credentials), ollama)
