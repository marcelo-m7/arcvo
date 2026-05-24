import { api } from "@/lib/api";

export type ProductionStatus = {
  branch: string;
  commit: string;
  dirty: boolean;
  coolify_health: Record<string, unknown>;
  coolify_api: Record<string, unknown>;
  ollama_ok: boolean;
  ollama_health: Record<string, unknown>;
  support: {
    available: boolean;
    helpdesk_total: number | null;
    helpdesk_open: number | null;
    helpdesk_sla_breached: number | null;
    knowledge_total: number | null;
    knowledge_published: number | null;
    error: string | null;
  };
};

export type CoolifyDeployResult = {
  configured: boolean;
  triggered: boolean;
  status_code: number | null;
  body: string | null;
};

export async function fetchProductionStatus() {
  const response = await api.get<ProductionStatus>("/api/v1/deploy/coolify/status");
  return response.data;
}

export async function triggerCoolifyDeploy() {
  const response = await api.post<CoolifyDeployResult>("/api/v1/deploy/coolify");
  return response.data;
}
