import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, CheckCircle2, ClipboardList, Loader2, MessageSquare } from "lucide-react";
import { FormEvent, useMemo, useState } from "react";

import {
  createHelpdeskComment,
  createHelpdeskTicket,
  fetchHelpdeskComments,
  fetchHelpdeskTickets,
  transitionHelpdeskTicket,
} from "@/lib/helpdesk";

type FormState = {
  name: string;
  priority: "0" | "1" | "2" | "3";
  taskId: string;
  assigneeAgentId: string;
};

const initialForm: FormState = {
  name: "",
  priority: "1",
  taskId: "",
  assigneeAgentId: "",
};

export function HelpdeskPage() {
  const queryClient = useQueryClient();
  const [selectedTicketId, setSelectedTicketId] = useState<number | null>(null);
  const [commentBody, setCommentBody] = useState("");
  const [form, setForm] = useState<FormState>(initialForm);

  const ticketsQuery = useQuery({
    queryKey: ["helpdesk-tickets"],
    queryFn: () => fetchHelpdeskTickets(),
  });

  const commentsQuery = useQuery({
    queryKey: ["helpdesk-comments", selectedTicketId],
    queryFn: () => fetchHelpdeskComments(selectedTicketId as number),
    enabled: Boolean(selectedTicketId),
  });

  const createTicket = useMutation({
    mutationFn: createHelpdeskTicket,
    onSuccess: () => {
      setForm(initialForm);
      void queryClient.invalidateQueries({ queryKey: ["helpdesk-tickets"] });
    },
  });

  const transitionTicket = useMutation({
    mutationFn: ({ ticketId, action }: { ticketId: number; action: "set_in_progress" | "set_resolved" }) =>
      transitionHelpdeskTicket(ticketId, action),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["helpdesk-tickets"] });
      if (selectedTicketId) {
        void queryClient.invalidateQueries({ queryKey: ["helpdesk-comments", selectedTicketId] });
      }
    },
  });

  const addComment = useMutation({
    mutationFn: ({ ticketId, body }: { ticketId: number; body: string }) =>
      createHelpdeskComment(ticketId, { body, comment_type: "note" }),
    onSuccess: () => {
      setCommentBody("");
      if (selectedTicketId) {
        void queryClient.invalidateQueries({ queryKey: ["helpdesk-comments", selectedTicketId] });
      }
    },
  });

  const tickets = useMemo(() => ticketsQuery.data ?? [], [ticketsQuery.data]);

  function onSubmitTicket(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    createTicket.mutate({
      name: form.name,
      priority: form.priority,
      task_id: form.taskId ? Number(form.taskId) : undefined,
      assignee_agent_id: form.assigneeAgentId ? Number(form.assigneeAgentId) : undefined,
    });
  }

  function onSubmitComment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedTicketId || !commentBody.trim()) return;
    addComment.mutate({ ticketId: selectedTicketId, body: commentBody.trim() });
  }

  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <section className="rounded-md bg-zinc-950 px-5 py-7 text-white sm:px-8">
        <div className="flex items-center gap-3">
          <ClipboardList className="h-6 w-6 text-yellow-200" aria-hidden />
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-yellow-200">
            arcvo helpdesk
          </p>
        </div>
        <h2 className="mt-3 text-3xl font-black sm:text-4xl">Suporte operacional no Odoo Community.</h2>
        <p className="mt-3 max-w-2xl text-sm text-white/75">
          Tickets, SLA e colaboração com agentes sem dependência de módulos enterprise.
        </p>
      </section>

      <section className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
        <div className="rounded-md border border-zinc-200 bg-white">
          <div className="flex items-center justify-between border-b border-zinc-200 px-4 py-3">
            <h3 className="text-sm font-semibold">Tickets</h3>
            {ticketsQuery.isFetching ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
          </div>
          <div className="divide-y divide-zinc-100">
            {tickets.map((ticket) => (
              <article
                key={ticket.id}
                className="cursor-pointer px-4 py-3 hover:bg-zinc-50"
                onClick={() => setSelectedTicketId(ticket.id)}
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="text-sm font-semibold text-zinc-900">
                    {ticket.ticket_ref ?? "-"} - {ticket.name}
                  </p>
                  <span className="rounded-full bg-zinc-100 px-2 py-1 text-xs font-medium text-zinc-700">
                    {ticket.state ?? "new"}
                  </span>
                </div>
                <div className="mt-2 flex flex-wrap gap-2">
                  <button
                    type="button"
                    className="inline-flex h-8 items-center gap-1 rounded-md border border-zinc-300 px-2 text-xs"
                    onClick={(event) => {
                      event.stopPropagation();
                      transitionTicket.mutate({ ticketId: ticket.id, action: "set_in_progress" });
                    }}
                  >
                    <AlertTriangle className="h-3.5 w-3.5" /> Iniciar
                  </button>
                  <button
                    type="button"
                    className="inline-flex h-8 items-center gap-1 rounded-md border border-zinc-300 px-2 text-xs"
                    onClick={(event) => {
                      event.stopPropagation();
                      transitionTicket.mutate({ ticketId: ticket.id, action: "set_resolved" });
                    }}
                  >
                    <CheckCircle2 className="h-3.5 w-3.5" /> Resolver
                  </button>
                </div>
              </article>
            ))}
            {!ticketsQuery.isLoading && tickets.length === 0 ? (
              <p className="px-4 py-8 text-sm text-zinc-500">Nenhum ticket cadastrado.</p>
            ) : null}
          </div>
        </div>

        <div className="space-y-6">
          <form onSubmit={onSubmitTicket} className="rounded-md border border-zinc-200 bg-white p-4">
            <h3 className="text-sm font-semibold">Novo ticket</h3>
            <div className="mt-3 space-y-3">
              <input
                value={form.name}
                onChange={(event) => setForm((curr) => ({ ...curr, name: event.target.value }))}
                placeholder="Resumo do problema"
                className="h-10 w-full rounded-md border border-zinc-300 px-3 text-sm"
              />
              <select
                value={form.priority}
                onChange={(event) =>
                  setForm((curr) => ({ ...curr, priority: event.target.value as FormState["priority"] }))
                }
                className="h-10 w-full rounded-md border border-zinc-300 px-3 text-sm"
              >
                <option value="0">Low</option>
                <option value="1">Normal</option>
                <option value="2">High</option>
                <option value="3">Urgent</option>
              </select>
              <input
                value={form.taskId}
                onChange={(event) => setForm((curr) => ({ ...curr, taskId: event.target.value }))}
                placeholder="ID da task (opcional)"
                className="h-10 w-full rounded-md border border-zinc-300 px-3 text-sm"
              />
              <input
                value={form.assigneeAgentId}
                onChange={(event) =>
                  setForm((curr) => ({ ...curr, assigneeAgentId: event.target.value }))
                }
                placeholder="ID do agente (opcional)"
                className="h-10 w-full rounded-md border border-zinc-300 px-3 text-sm"
              />
              <button
                type="submit"
                disabled={createTicket.isPending || !form.name.trim()}
                className="inline-flex h-10 w-full items-center justify-center rounded-md bg-zinc-950 text-sm font-semibold text-white disabled:opacity-60"
              >
                {createTicket.isPending ? "Criando..." : "Criar ticket"}
              </button>
            </div>
          </form>

          <form onSubmit={onSubmitComment} className="rounded-md border border-zinc-200 bg-white p-4">
            <div className="flex items-center gap-2">
              <MessageSquare className="h-4 w-4 text-emerald-700" />
              <h3 className="text-sm font-semibold">Comentários</h3>
            </div>
            <p className="mt-2 text-xs text-zinc-500">
              Ticket selecionado: {selectedTicketId ?? "nenhum"}
            </p>
            <textarea
              value={commentBody}
              onChange={(event) => setCommentBody(event.target.value)}
              rows={3}
              className="mt-3 w-full rounded-md border border-zinc-300 px-3 py-2 text-sm"
              placeholder="Adicionar comentário"
            />
            <button
              type="submit"
              disabled={!selectedTicketId || !commentBody.trim() || addComment.isPending}
              className="mt-3 inline-flex h-10 w-full items-center justify-center rounded-md bg-zinc-950 text-sm font-semibold text-white disabled:opacity-60"
            >
              {addComment.isPending ? "Salvando..." : "Salvar comentário"}
            </button>
            <div className="mt-4 space-y-2">
              {(commentsQuery.data ?? []).map((comment) => (
                <div key={comment.id} className="rounded-md border border-zinc-200 px-3 py-2 text-sm">
                  <p className="font-medium text-zinc-700">{comment.comment_type}</p>
                  <p className="mt-1 text-zinc-800">{comment.body}</p>
                </div>
              ))}
            </div>
          </form>
        </div>
      </section>
    </div>
  );
}
