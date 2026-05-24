import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bot, CheckCircle2, ClipboardList, Loader2, Play, Radio, Shield } from "lucide-react";
import { FormEvent, useMemo, useState } from "react";

import {
  assignAgentTask,
  fetchAgentAudit,
  fetchAgentExecutions,
  fetchAgents,
  recordAgentHeartbeat,
  runAgent,
  runPendingAgents,
  type AgentInfo,
} from "@/lib/agents";

export function AgentsPage() {
  const queryClient = useQueryClient();
  const [taskId, setTaskId] = useState("");
  const [agentId, setAgentId] = useState("");
  const [notes, setNotes] = useState("");

  const agents = useQuery({ queryKey: ["agents"], queryFn: fetchAgents });
  const audit = useQuery({ queryKey: ["agent-audit"], queryFn: fetchAgentAudit });
  const executions = useQuery({ queryKey: ["agent-executions"], queryFn: fetchAgentExecutions });

  const heartbeat = useMutation({
    mutationFn: recordAgentHeartbeat,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["agents"] });
      void queryClient.invalidateQueries({ queryKey: ["agent-audit"] });
    },
  });

  const assignment = useMutation({
    mutationFn: assignAgentTask,
    onSuccess: () => {
      setTaskId("");
      setNotes("");
      void queryClient.invalidateQueries({ queryKey: ["agents"] });
      void queryClient.invalidateQueries({ queryKey: ["agent-audit"] });
    },
  });

  const agentRun = useMutation({
    mutationFn: runAgent,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["agents"] });
      void queryClient.invalidateQueries({ queryKey: ["agent-audit"] });
      void queryClient.invalidateQueries({ queryKey: ["agent-executions"] });
    },
  });

  const runPending = useMutation({
    mutationFn: runPendingAgents,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["agents"] });
      void queryClient.invalidateQueries({ queryKey: ["agent-audit"] });
      void queryClient.invalidateQueries({ queryKey: ["agent-executions"] });
    },
  });

  const agentRows = useMemo(() => agents.data ?? [], [agents.data]);
  const availableCount = useMemo(
    () => agentRows.filter((agent) => agent.is_available).length,
    [agentRows],
  );

  function onAssign(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    assignment.mutate({
      agent_id: Number(agentId),
      task_id: Number(taskId),
      notes,
    });
  }

  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <section className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_360px]">
        <div className="overflow-hidden rounded-md bg-zinc-950 text-white">
          <div className="bg-[linear-gradient(120deg,rgba(16,185,129,.32),rgba(236,72,153,.24),rgba(250,204,21,.20))] px-5 py-7 sm:px-8">
            <div className="flex items-center gap-3">
              <Bot className="h-6 w-6 text-yellow-200" aria-hidden />
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-yellow-200">
                projetos odoo + arcvo agents
              </p>
            </div>
            <h2 className="mt-3 max-w-3xl text-3xl font-black leading-tight sm:text-4xl">
              Agentes rastreaveis, tarefas no Odoo, operacao sem fantasia.
            </h2>
            <p className="mt-4 max-w-2xl text-sm leading-6 text-white/78">
              Esta area administra o contrato real `arcvo.*`: registro, disponibilidade,
              heartbeat, atribuicoes e auditoria.
            </p>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <Metric label="Agentes" value={agentRows.length} icon={Bot} />
          <Metric label="Disponiveis" value={availableCount} icon={CheckCircle2} />
          <Metric
            label="Abertas"
            value={agentRows.reduce((sum, agent) => sum + agent.open_assignment_count, 0)}
            icon={ClipboardList}
          />
          <Metric label="Auditoria" value={audit.data?.length ?? 0} icon={Shield} />
        </div>
      </section>

      <section className="rounded-md border border-zinc-200 bg-white p-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h3 className="text-sm font-semibold">Ciclo autonomo</h3>
            <p className="mt-1 text-sm text-zinc-500">
              Executa atribuicoes abertas com Ollama, allowlist de comandos e auditoria no Odoo.
            </p>
          </div>
          <button
            type="button"
            onClick={() => runPending.mutate()}
            disabled={runPending.isPending}
            className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-zinc-950 px-3 text-sm font-semibold text-white hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {runPending.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
            ) : (
              <Play className="h-4 w-4" aria-hidden />
            )}
            Rodar pendentes
          </button>
        </div>
        {runPending.isError ? (
          <p className="mt-3 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
            Falha ao executar agentes. Verifique se `arcvo_agents` esta instalado e se Ollama responde.
          </p>
        ) : null}
      </section>

      <section className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_380px]">
        <div className="rounded-md border border-zinc-200 bg-white">
          <div className="flex items-center justify-between border-b border-zinc-200 px-4 py-3">
            <h3 className="text-sm font-semibold">Agentes</h3>
            {agents.isFetching ? <Loader2 className="h-4 w-4 animate-spin text-zinc-500" /> : null}
          </div>
          <div className="divide-y divide-zinc-100">
            {agentRows.map((agent) => (
              <AgentRow
                key={agent.id}
                agent={agent}
                onHeartbeat={() => heartbeat.mutate(agent.id)}
                onRun={() => agentRun.mutate(agent.id)}
                heartbeatPending={heartbeat.isPending}
                runPending={agentRun.isPending}
              />
            ))}
            {!agents.isLoading && agentRows.length === 0 ? (
              <p className="px-4 py-8 text-sm text-zinc-500">
                Nenhum agente `arcvo.agent` encontrado no Odoo remoto.
              </p>
            ) : null}
          </div>
        </div>

        <div className="space-y-6">
          <form onSubmit={onAssign} className="rounded-md border border-zinc-200 bg-white p-4">
            <div className="flex items-center gap-2">
              <ClipboardList className="h-4 w-4 text-emerald-700" aria-hidden />
              <h3 className="text-sm font-semibold">Vincular tarefa</h3>
            </div>
            <div className="mt-4 space-y-3">
              <label className="block">
                <span className="text-sm font-medium text-zinc-700">Agente</span>
                <select
                  value={agentId}
                  onChange={(event) => setAgentId(event.target.value)}
                  className="mt-2 h-10 w-full rounded-md border border-zinc-300 bg-white px-3 text-sm outline-none ring-emerald-600 focus:ring-2"
                >
                  <option value="">Selecione</option>
                  {agentRows.map((agent) => (
                    <option key={agent.id} value={agent.id}>
                      {agent.name}
                    </option>
                  ))}
                </select>
              </label>
              <label className="block">
                <span className="text-sm font-medium text-zinc-700">ID da tarefa Odoo</span>
                <input
                  type="number"
                  min="1"
                  value={taskId}
                  onChange={(event) => setTaskId(event.target.value)}
                  className="mt-2 h-10 w-full rounded-md border border-zinc-300 px-3 text-sm outline-none ring-emerald-600 focus:ring-2"
                />
              </label>
              <label className="block">
                <span className="text-sm font-medium text-zinc-700">Notas</span>
                <textarea
                  value={notes}
                  onChange={(event) => setNotes(event.target.value)}
                  rows={3}
                  className="mt-2 w-full rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none ring-emerald-600 focus:ring-2"
                />
              </label>
              {assignment.isError ? (
                <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
                  Nao foi possivel vincular a tarefa. Confirme se o addon `arcvo_agents`
                  esta instalado no Odoo remoto.
                </p>
              ) : null}
              <button
                type="submit"
                disabled={assignment.isPending || !agentId || !taskId}
                className="inline-flex h-10 w-full items-center justify-center gap-2 rounded-md bg-zinc-950 px-3 text-sm font-semibold text-white hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {assignment.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
                ) : (
                  <ClipboardList className="h-4 w-4" aria-hidden />
                )}
                Vincular no Odoo
              </button>
            </div>
          </form>

          <div className="rounded-md border border-zinc-200 bg-white">
            <div className="border-b border-zinc-200 px-4 py-3">
              <h3 className="text-sm font-semibold">Auditoria recente</h3>
            </div>
            <div className="max-h-[360px] divide-y divide-zinc-100 overflow-auto">
              {(audit.data ?? []).map((entry) => (
                <div key={entry.id} className="px-4 py-3">
                  <p className="text-sm font-medium text-zinc-900">{entry.action}</p>
                  <p className="mt-1 text-xs text-zinc-500">{entry.message || "Sem mensagem"}</p>
                  <p className="mt-1 text-[11px] text-zinc-400">{entry.created_at}</p>
                </div>
              ))}
              {!audit.isLoading && (audit.data ?? []).length === 0 ? (
                <p className="px-4 py-8 text-sm text-zinc-500">Sem auditoria registrada.</p>
              ) : null}
            </div>
          </div>

          <div className="rounded-md border border-zinc-200 bg-white">
            <div className="border-b border-zinc-200 px-4 py-3">
              <h3 className="text-sm font-semibold">Execucoes recentes</h3>
            </div>
            <div className="max-h-[300px] divide-y divide-zinc-100 overflow-auto">
              {(executions.data ?? []).map((entry) => (
                <div key={entry.id} className="px-4 py-3">
                  <p className="text-sm font-medium text-zinc-900">{entry.action}</p>
                  <p className="mt-1 text-xs text-zinc-500">{entry.message || "Sem resumo"}</p>
                  <p className="mt-1 text-[11px] text-zinc-400">{entry.created_at}</p>
                </div>
              ))}
              {!executions.isLoading && (executions.data ?? []).length === 0 ? (
                <p className="px-4 py-8 text-sm text-zinc-500">Sem execucoes registradas.</p>
              ) : null}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

function AgentRow({
  agent,
  onHeartbeat,
  onRun,
  heartbeatPending,
  runPending,
}: {
  agent: AgentInfo;
  onHeartbeat: () => void;
  onRun: () => void;
  heartbeatPending: boolean;
  runPending: boolean;
}) {
  return (
    <div className="grid gap-4 px-4 py-4 md:grid-cols-[minmax(0,1fr)_auto] md:items-center">
      <div>
        <div className="flex flex-wrap items-center gap-2">
          <h4 className="text-sm font-semibold text-zinc-950">{agent.name}</h4>
          <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-800">
            {agent.role}
          </span>
          <span className="rounded-full bg-zinc-100 px-2 py-0.5 text-xs font-medium text-zinc-700">
            {agent.state}
          </span>
        </div>
        <p className="mt-2 text-sm leading-6 text-zinc-600">
          {agent.description || "Sem descricao registrada."}
        </p>
        <div className="mt-3 flex flex-wrap gap-3 text-xs text-zinc-500">
          <span>{agent.open_assignment_count} abertas</span>
          <span>{agent.completed_assignment_count} concluidas</span>
          <span>{agent.success_rate.toFixed(1)}% sucesso</span>
          <span>{agent.last_heartbeat || "sem heartbeat"}</span>
        </div>
      </div>
      <div className="flex flex-wrap gap-2 md:justify-end">
        <button
          type="button"
          onClick={onRun}
          disabled={runPending}
          className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-emerald-700 px-3 text-sm font-medium text-white hover:bg-emerald-800 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {runPending ? (
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
          ) : (
            <Play className="h-4 w-4" aria-hidden />
          )}
          Rodar
        </button>
        <button
          type="button"
          onClick={onHeartbeat}
          disabled={heartbeatPending}
          className="inline-flex h-10 items-center justify-center gap-2 rounded-md border border-zinc-300 px-3 text-sm font-medium text-zinc-700 hover:bg-zinc-50 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {heartbeatPending ? (
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
          ) : (
            <Radio className="h-4 w-4" aria-hidden />
          )}
          Heartbeat
        </button>
      </div>
    </div>
  );
}

function Metric({
  label,
  value,
  icon: Icon,
}: {
  label: string;
  value: number;
  icon: typeof Bot;
}) {
  return (
    <div className="rounded-md border border-zinc-200 bg-white p-4">
      <Icon className="h-4 w-4 text-pink-600" aria-hidden />
      <p className="mt-3 text-2xl font-black text-zinc-950">{value}</p>
      <p className="text-xs font-medium text-zinc-500">{label}</p>
    </div>
  );
}
