import { useMutation } from "@tanstack/react-query";
import { LockKeyhole, Sparkles } from "lucide-react";
import { FormEvent, useState } from "react";
import { Navigate } from "react-router-dom";

import { login } from "@/lib/archive";
import { useAuthStore } from "@/store/auth";

export function LoginPage() {
  const [password, setPassword] = useState("");
  const setToken = useAuthStore((state) => state.setToken);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  const loginMutation = useMutation({
    mutationFn: login,
    onSuccess: (data) => setToken(data.access_token),
  });

  if (isAuthenticated) {
    return <Navigate to="/acervo" replace />;
  }

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    loginMutation.mutate(password);
  }

  return (
    <main className="min-h-screen bg-[#fbf7ef] text-zinc-950">
      <div className="grid min-h-screen lg:grid-cols-[1fr_480px]">
        <section className="relative flex min-h-[52vh] items-end overflow-hidden bg-zinc-950 p-8 text-white lg:min-h-screen lg:p-12">
          <img
            src="https://images.unsplash.com/photo-1516280440614-37939bbacd81?auto=format&fit=crop&w=1600&q=80"
            alt=""
            className="absolute inset-0 h-full w-full object-cover opacity-55"
          />
          <div className="absolute inset-0 bg-[linear-gradient(120deg,rgba(8,20,20,.9),rgba(8,20,20,.25)_55%,rgba(255,193,7,.25))]" />
          <div className="relative max-w-3xl">
            <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-white/30 px-3 py-1 text-xs font-medium uppercase tracking-[0.18em]">
              <Sparkles className="h-3.5 w-3.5 text-yellow-300" aria-hidden />
              pajuba, axe, memoria viva
            </div>
            <h1 className="max-w-2xl text-5xl font-black leading-none sm:text-6xl lg:text-7xl">
              Arcvo
            </h1>
            <p className="mt-5 max-w-xl text-lg text-white/85">
              Um painel para organizar videos do YouTube como cursos no eLearning do Odoo.
            </p>
          </div>
        </section>

        <section className="flex items-center px-6 py-10 sm:px-10">
          <form onSubmit={onSubmit} className="w-full space-y-6">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.2em] text-emerald-700">
                administracao
              </p>
              <h2 className="mt-2 text-3xl font-bold">Entrar no acervo</h2>
              <p className="mt-2 text-sm text-zinc-600">
                Use a senha local configurada no ambiente do backend.
              </p>
            </div>

            <label className="block">
              <span className="text-sm font-medium text-zinc-700">Senha</span>
              <input
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                type="password"
                autoComplete="current-password"
                className="mt-2 h-12 w-full rounded-md border border-zinc-300 bg-white px-3 text-base outline-none ring-emerald-600 focus:ring-2"
              />
            </label>

            {loginMutation.isError ? (
              <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
                Senha invalida.
              </p>
            ) : null}

            <button
              type="submit"
              disabled={loginMutation.isPending}
              className="inline-flex h-12 w-full items-center justify-center gap-2 rounded-md bg-zinc-950 px-4 text-sm font-semibold text-white hover:bg-zinc-800 disabled:cursor-wait disabled:opacity-70"
            >
              <LockKeyhole className="h-4 w-4" aria-hidden />
              {loginMutation.isPending ? "Entrando..." : "Entrar"}
            </button>
          </form>
        </section>
      </div>
    </main>
  );
}
