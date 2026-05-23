import { Activity, Archive, Database } from "lucide-react";
import { NavLink, Outlet } from "react-router-dom";

const navItems = [{ to: "/odoo", label: "Odoo", icon: Database }];

export function Shell() {
  return (
    <div className="min-h-screen bg-zinc-50 text-zinc-950">
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-zinc-200 bg-white lg:block">
        <div className="flex h-16 items-center gap-3 border-b border-zinc-200 px-5">
          <Archive className="h-6 w-6 text-emerald-700" aria-hidden />
          <div>
            <p className="text-sm font-semibold leading-5">Arcvo</p>
            <p className="text-xs text-zinc-500">Digital archive admin</p>
          </div>
        </div>
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
      </aside>

      <div className="lg:pl-64">
        <header className="flex h-16 items-center justify-between border-b border-zinc-200 bg-white px-4 sm:px-6">
          <div className="flex items-center gap-3">
            <Activity className="h-5 w-5 text-emerald-700" aria-hidden />
            <div>
              <h1 className="text-base font-semibold">Operations</h1>
              <p className="text-xs text-zinc-500">API, Odoo and integration status</p>
            </div>
          </div>
        </header>
        <main className="px-4 py-6 sm:px-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
