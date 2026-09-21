import React, { useEffect, useState } from "react";
import { Navigate, Outlet } from "react-router-dom";
import { apiFetch } from "../api/apiFetch";

export default function ProtectedRoute() {
  const [checking, setChecking] = useState(true);
  const [authenticated, setAuthenticated] = useState(false);

  useEffect(() => {
    apiFetch("/auth/me")
      .then((response) => {
        setAuthenticated(response.ok);
      })
      .catch(() => {
        setAuthenticated(false);
      })
      .finally(() => {
        setChecking(false);
      });
  }, []);

  if (checking) {
    return <div>Checking authentication...</div>;
  }

  if (!authenticated) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}
