import { Activity, Archive, Bot, Clapperboard, Database, LogOut, Rocket } from "lucide-react";
import { NavLink, Outlet } from "react-router-dom";

import { useAuthStore } from "@/store/auth";

const navItems = [
  { to: "/acervo", label: "Acervo", icon: Clapperboard },
  { to: "/agentes", label: "Agentes", icon: Bot },
  { to: "/producao", label: "Producao", icon: Rocket },
  { to: "/odoo", label: "Odoo", icon: Database },
];

export function Shell() {
  const logout = useAuthStore((state) => state.logout);

  return (
    <div className="min-h-screen bg-[#f8f7f2] text-zinc-950">
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-zinc-200 bg-white lg:block">
        <div className="flex h-16 items-center gap-3 border-b border-zinc-200 px-5">
          <Archive className="h-6 w-6 text-emerald-700" aria-hidden />
          <div>
            <p className="text-sm font-semibold leading-5">Arcvo</p>
            <p className="text-xs text-zinc-500">Odoo remoto</p>
          </div>
        </div>
        <div className="flex h-[calc(100%-4rem)] flex-col justify-between">
          <nav className="space-y-1 px-3 py-4">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    [
                      "flex h-10 items-center gap-3 rounded-md px-3 text-sm font-medium",
                      isActive
                        ? "bg-emerald-50 text-emerald-800"
                        : "text-zinc-600 hover:bg-zinc-100 hover:text-zinc-950",
                    ].join(" ")
                  }
                >
                  <Icon className="h-4 w-4" aria-hidden />
                  {item.label}
                </NavLink>
              );
            })}
          </nav>
          <div className="border-t border-zinc-200 p-3">
            <button
              type="button"
              onClick={logout}
              className="flex h-10 w-full items-center gap-3 rounded-md px-3 text-sm font-medium text-zinc-600 hover:bg-zinc-100 hover:text-zinc-950"
            >
              <LogOut className="h-4 w-4" aria-hidden />
              Sair
            </button>
          </div>
        </div>
      </aside>

      <div className="lg:pl-64">
        <header className="flex h-16 items-center justify-between border-b border-zinc-200 bg-white px-4 sm:px-6">
          <div className="flex items-center gap-3">
            <Activity className="h-5 w-5 text-emerald-700" aria-hidden />
            <div>
              <h1 className="text-base font-semibold">Acervo Admin</h1>
              <p className="text-xs text-zinc-500">Acervo, agentes e eLearning</p>
            </div>
          </div>
          <button
            type="button"
            onClick={logout}
            className="inline-flex h-9 items-center gap-2 rounded-md border border-zinc-300 px-3 text-sm font-medium text-zinc-700 hover:bg-zinc-50 lg:hidden"
          >
            <LogOut className="h-4 w-4" aria-hidden />
            Sair
          </button>
        </header>
        <main className="px-4 py-6 sm:px-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
