import { api } from "@/lib/api";

export type HelpdeskTicket = {
  id: number;
  ticket_ref: string | null;
  name: string;
  state: string | null;
  priority: string;
  stage: [number, string] | null;
  assignee_agent: [number, string] | null;
  task: [number, string] | null;
  sla_deadline: string | null;
  sla_breached: boolean;
};

export type HelpdeskComment = {
  id: number;
  ticket_id: number;
  author_id: [number, string] | null;
  comment_type: string;
  body: string;
  created_at: string | null;
};

export async function fetchHelpdeskTickets(state?: string) {
  const response = await api.get<HelpdeskTicket[]>("/api/v1/helpdesk/tickets", {
    params: state ? { state } : {},
  });
  return response.data;
}

export async function createHelpdeskTicket(payload: {
  name: string;
  priority: "0" | "1" | "2" | "3";
  task_id?: number;
  assignee_agent_id?: number;
  description?: string;
}) {
  const response = await api.post<HelpdeskTicket>("/api/v1/helpdesk/tickets", payload);
  return response.data;
}

export async function transitionHelpdeskTicket(
  ticketId: number,
  action:
    | "set_in_progress"
    | "set_blocked"
    | "set_resolved"
    | "set_closed"
    | "reopen"
    | "record_first_response"
    | "assign_agent",
  note?: string,
) {
  const response = await api.post<HelpdeskTicket>(`/api/v1/helpdesk/tickets/${ticketId}/transition`, {
    action,
    note,
  });
  return response.data;
}

export async function fetchHelpdeskComments(ticketId: number) {
  const response = await api.get<HelpdeskComment[]>(`/api/v1/helpdesk/tickets/${ticketId}/comments`);
  return response.data;
}

export async function createHelpdeskComment(
  ticketId: number,
  payload: { body: string; comment_type?: "note" | "public" | "internal" | "system" },
) {
  const response = await api.post<HelpdeskComment>(`/api/v1/helpdesk/tickets/${ticketId}/comments`, payload);
  return response.data;
}
