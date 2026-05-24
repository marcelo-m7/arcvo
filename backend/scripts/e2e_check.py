"""End-to-end system check for Arcvo.

Validates: login → agents from Odoo → deploy/Ollama status → audit trail.
Optionally creates a test task and runs an agent on it when --run-agent is passed.
Usage:
    uv run python scripts/e2e_check.py
    uv run python scripts/e2e_check.py --run-agent
"""
import asyncio
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).parents[2] / ".env")

import os  # noqa: E402

BASE = "http://127.0.0.1:8000"
ADMIN_PASSWORD = os.getenv("APP_ADMIN_PASSWORD", "admin_arcvo_2026_secure_password")
RUN_AGENT = "--run-agent" in sys.argv

_OK = "✅"
_FAIL = "❌"


async def main() -> None:
    errors: list[str] = []

    async with httpx.AsyncClient(timeout=60) as client:
        # 1. Login
        login = await client.post(
            f"{BASE}/api/v1/auth/login",
            json={"username": "admin", "password": ADMIN_PASSWORD},
        )
        if login.status_code != 200:
            print(f"{_FAIL} Login failed: {login.status_code} {login.text}")
            sys.exit(1)
        token = login.json()["access_token"]
        h = {"Authorization": f"Bearer {token}"}
        print(f"{_OK} Login")

        # 2. Agents (from Odoo SSOT)
        agents_resp = await client.get(f"{BASE}/api/v1/agents", headers=h)
        if agents_resp.status_code != 200:
            errors.append(f"agents: {agents_resp.status_code}")
            print(f"{_FAIL} Agents: {agents_resp.status_code} {agents_resp.text[:200]}")
        else:
            agents = agents_resp.json()
            print(f"{_OK} Agents ({len(agents)}): {[a['name'] for a in agents]}")

        # 3. Production / deploy status
        deploy_resp = await client.get(f"{BASE}/api/v1/deploy/coolify/status", headers=h)
        if deploy_resp.status_code != 200:
            errors.append(f"deploy: {deploy_resp.status_code}")
            print(f"{_FAIL} Deploy status: {deploy_resp.status_code}")
        else:
            d = deploy_resp.json()
            print(
                f"{_OK} Deploy — branch={d['branch']} commit={d['commit']} dirty={d['dirty']}"
            )
            ollama_icon = _OK if d["ollama_ok"] else _FAIL
            coolify_icon = _OK if d["coolify_health"]["healthy"] else _FAIL
            print(f"   {coolify_icon} Coolify healthy={d['coolify_health']['healthy']}")
            print(f"   {ollama_icon} Ollama ok={d['ollama_ok']}")
            if not d["ollama_ok"]:
                errors.append("ollama unreachable")

        # 4. Odoo health
        odoo_resp = await client.get(f"{BASE}/api/v1/odoo/health", headers=h)
        if odoo_resp.status_code == 200:
            odoo = odoo_resp.json()
            print(f"{_OK} Odoo health: version={odoo.get('version','?')} uid={odoo.get('uid','?')}")
        else:
            errors.append(f"odoo_health: {odoo_resp.status_code}")
            print(f"{_FAIL} Odoo health: {odoo_resp.status_code}")

        # 5. Audit trail
        audit_resp = await client.get(f"{BASE}/api/v1/agents/audit?limit=5", headers=h)
        if audit_resp.status_code == 200:
            audit = audit_resp.json()
            print(f"{_OK} Audit entries: {len(audit)}")
            for entry in audit[:3]:
                msg = (entry.get("message") or "")[:80]
                print(f"   [{entry['action']}] {msg}")
        else:
            errors.append(f"audit: {audit_resp.status_code}")
            print(f"{_FAIL} Audit: {audit_resp.status_code}")

        # 6. Optional: create test task and run agent cycle
        if RUN_AGENT and agents_resp.status_code == 200 and agents:
            print("\n--- Running agent execution cycle ---")
            # Pick Backend Operator or first available agent
            target = next(
                (a for a in agents if "backend" in a["name"].lower() and a["is_available"]),
                next((a for a in agents if a["is_available"]), None),
            )
            if not target:
                print(f"{_FAIL} No available agent to run")
            else:
                agent_id = target["id"]
                print(f"   Using agent: {target['name']} (id={agent_id})")

                # Create a test task in Odoo project via the Odoo generic endpoint
                task_resp = await client.post(
                    f"{BASE}/api/v1/odoo/models/project.task/records",
                    headers=h,
                    json={
                        "values": {
                            "name": "[ARCVO-E2E] Automated test task",
                            "description": (
                                "Created by e2e_check.py for agent execution validation."
                            ),
                        }
                    },
                )
                if task_resp.status_code != 200:
                    print(
                        f"{_FAIL} Could not create test task: "
                        f"{task_resp.status_code} {task_resp.text[:200]}"
                    )
                    errors.append("create_task failed")
                else:
                    task_id = task_resp.json().get("id")
                    print(f"   {_OK} Test task created: id={task_id}")

                    # Assign agent to task
                    assign_resp = await client.post(
                        f"{BASE}/api/v1/agents/tasks/{task_id}/assign",
                        headers=h,
                        json={"agent_id": agent_id, "notes": "e2e automated test"},
                    )
                    if assign_resp.status_code != 200:
                        print(
                            f"{_FAIL} Assignment failed: "
                            f"{assign_resp.status_code} {assign_resp.text[:200]}"
                        )
                        errors.append("assign_task failed")
                    else:
                        assign = assign_resp.json()
                        print(f"   {_OK} Assignment created: id={assign['assignment_id']}")

                        # Run agent (calls Ollama for decision)
                        run_resp = await client.post(
                            f"{BASE}/api/v1/agents/{agent_id}/run",
                            headers=h,
                            json={"limit": 1},
                        )
                        if run_resp.status_code != 200:
                            print(
                                f"{_FAIL} Agent run failed: "
                                f"{run_resp.status_code} {run_resp.text[:300]}"
                            )
                            errors.append("agent_run failed")
                        else:
                            executions = run_resp.json()
                            for ex in executions:
                                print(
                                    f"   {_OK} Execution: status={ex['status']} "
                                    f"progress={ex['progress']}% summary={ex['summary'][:80]}"
                                )

    if errors:
        print(f"\n{_FAIL} Completed with errors: {errors}")
        sys.exit(1)
    else:
        print(f"\n{_OK} All checks passed")


if __name__ == "__main__":
    asyncio.run(main())

