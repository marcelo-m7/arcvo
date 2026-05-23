import { useQuery } from "@tanstack/react-query";
import { RefreshCw, Server, ShieldCheck, TriangleAlert } from "lucide-react";

import { api } from "@/lib/api";

type OdooHealth = {
  status: string;
  integration_mode: string;
  url: string;
  database: string;
  server_version: string | null;
  authenticated: boolean;
  uid: number | null;
  partner_count: number | null;
  mcp_mode: string | null;
  tls_workaround_enabled: boolean;
};

async function fetchOdooHealth() {
  const response = await api.get<OdooHealth>("/api/v1/odoo/health");
  return response.data;
}

export function OdooHealthPage() {
  const health = useQuery({
    queryKey: ["odoo-health"],
    queryFn: fetchOdooHealth,
  });

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <section className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-2xl font-semibold tracking-normal">Odoo integration</h2>
          <p className="mt-1 text-sm text-zinc-600">
            Runtime status for the Odoo 19 connection used by the Arcvo API.
          </p>
        </div>
        <button
          type="button"
          onClick={() => void health.refetch()}
          className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-zinc-950 px-4 text-sm font-medium text-white hover:bg-zinc-800"
        >
          <RefreshCw className="h-4 w-4" aria-hidden />
          Refresh
        </button>
      </section>

      {health.isError ? (
        <div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-800">
          <div className="flex items-center gap-2 font-medium">
            <TriangleAlert className="h-4 w-4" aria-hidden />
            Odoo healthcheck failed
          </div>
          <p className="mt-2 text-red-700">
            Check the backend logs, Odoo credentials and the current Traefik certificate.
          </p>
        </div>
      ) : null}

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Metric label="Status" value={health.data?.status ?? "loading"} />
        <Metric label="Odoo" value={health.data?.server_version ?? "unknown"} />
        <Metric label="Database" value={health.data?.database ?? "unknown"} />
        <Metric label="Partners" value={String(health.data?.partner_count ?? "-")} />
      </section>

      <section className="rounded-md border border-zinc-200 bg-white">
        <div className="flex items-center gap-2 border-b border-zinc-200 px-4 py-3">
          <Server className="h-4 w-4 text-emerald-700" aria-hidden />
          <h3 className="text-sm font-semibold">Connection details</h3>
        </div>
        <dl className="grid gap-px bg-zinc-200 sm:grid-cols-2">
          <Detail label="URL" value={health.data?.url ?? "-"} />
          <Detail label="Integration mode" value={health.data?.integration_mode ?? "-"} />
          <Detail label="Authenticated" value={health.data?.authenticated ? "yes" : "no"} />
          <Detail label="MCP mode" value={health.data?.mcp_mode ?? "-"} />
          <Detail
            label="TLS workaround"
            value={health.data?.tls_workaround_enabled ? "enabled" : "disabled"}
          />
          <Detail label="UID" value={String(health.data?.uid ?? "-")} />
        </dl>
      </section>

      <section className="rounded-md border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
        <div className="flex items-center gap-2 font-medium">
          <ShieldCheck className="h-4 w-4" aria-hidden />
          Security note
        </div>
        <p className="mt-2">
          The TLS workaround should remain enabled only while the Odoo endpoint serves the
          Traefik default certificate.
        </p>
      </section>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-zinc-200 bg-white p-4">
      <p className="text-xs font-medium uppercase text-zinc-500">{label}</p>
      <p className="mt-2 break-words text-xl font-semibold">{value}</p>
    </div>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-white p-4">
      <dt className="text-xs font-medium uppercase text-zinc-500">{label}</dt>
      <dd className="mt-1 break-words text-sm text-zinc-900">{value}</dd>
    </div>
  );
}
