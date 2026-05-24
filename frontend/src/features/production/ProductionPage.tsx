import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { GitBranch, Loader2, Rocket, ServerCog, ShieldCheck, Terminal } from "lucide-react";

import { fetchProductionStatus, triggerCoolifyDeploy } from "@/lib/deploy";

export function ProductionPage() {
  const queryClient = useQueryClient();
  const status = useQuery({
    queryKey: ["production-status"],
    queryFn: fetchProductionStatus,
    refetchInterval: 30_000,
  });
  const deploy = useMutation({
    mutationFn: triggerCoolifyDeploy,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["production-status"] });
    },
  });
  const data = status.data;

  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <section className="rounded-md bg-zinc-950 px-5 py-7 text-white sm:px-8">
        <div className="flex items-center gap-3">
          <Rocket className="h-6 w-6 text-yellow-200" aria-hidden />
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-yellow-200">
            producao + coolify
          </p>
        </div>
        <h2 className="mt-3 text-3xl font-black sm:text-4xl">Mesa de deploy controlado.</h2>
        <p className="mt-4 max-w-2xl text-sm leading-6 text-white/75">
          Estado do repositorio, health do Coolify, Ollama e gatilho manual de deploy.
        </p>
      </section>

      <section className="grid gap-4 md:grid-cols-4">
        <StatusCard icon={GitBranch} label="Branch" value={data?.branch ?? "-"} />
        <StatusCard icon={Terminal} label="Commit" value={data?.commit ?? "-"} />
        <StatusCard icon={ShieldCheck} label="Worktree" value={data?.dirty ? "dirty" : "clean"} />
        <StatusCard icon={ServerCog} label="Ollama" value={data?.ollama_ok ? "ok" : "erro"} />
      </section>

      <section className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
        <div className="rounded-md border border-zinc-200 bg-white">
          <div className="border-b border-zinc-200 px-4 py-3">
            <h3 className="text-sm font-semibold">Diagnostico</h3>
          </div>
          <pre className="max-h-[520px] overflow-auto p-4 text-xs text-zinc-700">
            {JSON.stringify(data ?? {}, null, 2)}
          </pre>
        </div>

        <div className="rounded-md border border-zinc-200 bg-white p-4">
          <h3 className="text-sm font-semibold">Deploy Coolify</h3>
          <p className="mt-2 text-sm leading-6 text-zinc-500">
            Dispara o webhook configurado. Use depois de validacoes e push na branch `main`.
          </p>
          <button
            type="button"
            onClick={() => deploy.mutate()}
            disabled={deploy.isPending}
            className="mt-4 inline-flex h-10 w-full items-center justify-center gap-2 rounded-md bg-zinc-950 px-3 text-sm font-semibold text-white hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {deploy.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
            ) : (
              <Rocket className="h-4 w-4" aria-hidden />
            )}
            Disparar webhook
          </button>
          {deploy.data ? (
            <pre className="mt-4 max-h-[220px] overflow-auto rounded-md bg-zinc-50 p-3 text-xs text-zinc-700">
              {JSON.stringify(deploy.data, null, 2)}
            </pre>
          ) : null}
          {deploy.isError ? (
            <p className="mt-4 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
              Falha ao disparar webhook Coolify.
            </p>
          ) : null}
        </div>
      </section>
    </div>
  );
}

function StatusCard({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof GitBranch;
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-md border border-zinc-200 bg-white p-4">
      <Icon className="h-4 w-4 text-emerald-700" aria-hidden />
      <p className="mt-3 truncate text-lg font-black text-zinc-950">{value}</p>
      <p className="text-xs font-medium text-zinc-500">{label}</p>
    </div>
  );
}
