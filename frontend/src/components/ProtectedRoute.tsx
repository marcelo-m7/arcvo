import { Navigate, Outlet } from "react-router-dom";

import { useAuthStore } from "@/store/auth";

export function ProtectedRoute() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  return isAuthenticated ? <Outlet /> : <Navigate to="/login" replace />;
}
