import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { ProtectedRoute } from "@/components/ProtectedRoute";
import { Shell } from "@/components/Shell";
import { AgentsPage } from "@/features/agents/AgentsPage";
import { ArchivePage } from "@/features/archive/ArchivePage";
import { LoginPage } from "@/features/auth/LoginPage";
import { OdooHealthPage } from "@/features/odoo/OdooHealthPage";
import { ProductionPage } from "@/features/production/ProductionPage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
    },
  },
});

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route element={<ProtectedRoute />}>
            <Route element={<Shell />}>
              <Route index element={<Navigate to="/acervo" replace />} />
              <Route path="/acervo" element={<ArchivePage />} />
              <Route path="/agentes" element={<AgentsPage />} />
              <Route path="/odoo" element={<OdooHealthPage />} />
              <Route path="/producao" element={<ProductionPage />} />
            </Route>
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
