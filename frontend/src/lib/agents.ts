import { api } from "@/lib/api";

export type AgentInfo = {
  id: number;
  name: string;
  role: string;
  state: string;
  description: string | null;
  capability_ids: number[];
  max_concurrent_tasks: number;
  open_assignment_count: number;
  completed_assignment_count: number;
  success_rate: number;
  is_available: boolean;
  last_heartbeat: string | null;
};

export type AgentAuditLog = {
  id: number;
  agent_id: [number, string] | number | false | null;
  task_id: [number, string] | number | false | null;
  assignment_id: [number, string] | number | false | null;
  action: string;
  message: string | null;
  created_at: string | null;
};

export type AgentAssignment = {
  assignment_id: number;
  task_id: number;
  agent_id: number;
  status: string;
  created: boolean;
};

export type AgentExecution = {
  assignment_id: number;
  agent_id: number;
  task_id: number;
  status: string;
  progress: number;
  summary: string;
  command: string | null;
  command_allowed: boolean | null;
};

export async function fetchAgents() {
  const response = await api.get<AgentInfo[]>("/api/v1/agents");
  return response.data;
}

export async function fetchAgentAudit() {
  const response = await api.get<AgentAuditLog[]>("/api/v1/agents/audit");
  return response.data;
}

export async function recordAgentHeartbeat(agentId: number) {
  const response = await api.post(`/api/v1/agents/${agentId}/heartbeat`, {
    state: "idle",
    message: "Heartbeat from Arcvo Admin.",
  });
  return response.data;
}

export async function assignAgentTask(payload: { agent_id: number; task_id: number; notes: string }) {
  const response = await api.post<AgentAssignment>(
    `/api/v1/agents/tasks/${payload.task_id}/assign`,
    {
      agent_id: payload.agent_id,
      notes: payload.notes,
    },
  );
  return response.data;
}

export async function runAgent(agentId: number) {
  const response = await api.post<AgentExecution[]>(`/api/v1/agents/${agentId}/run`, {
    limit: 1,
  });
  return response.data;
}

export async function runPendingAgents() {
  const response = await api.post<AgentExecution[]>("/api/v1/agents/run-pending", {
    limit: 5,
  });
  return response.data;
}

export async function fetchAgentExecutions() {
  const response = await api.get<AgentAuditLog[]>("/api/v1/agents/executions");
  return response.data;
}

export type AgentChatResponse = {
  agent_id: number;
  agent_name: string;
  role: string;
  reply: string;
};

export async function chatWithAgent(agentId: number, message: string) {
  const response = await api.post<AgentChatResponse>(`/api/v1/agents/${agentId}/chat`, {
    message,
  });
  return response.data;
}
