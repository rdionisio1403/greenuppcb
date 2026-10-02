import React, { useEffect, useState } from "react";
import { Navigate, Outlet } from "react-router-dom";
import { apiFetch } from "../api/apiFetch";

export default function ProtectedRoute() {
  const [checking, setChecking] = useState(true);
  const [user, setUser] = useState(null);

  useEffect(() => {
    apiFetch("/auth/me")
      .then(async (response) => {
        if (!response.ok) {
          setUser(null);
          return;
        }

        const data = await response.json();
        setUser(data);
      })
      .catch(() => {
        setUser(null);
      })
      .finally(() => {
        setChecking(false);
      });
  }, []);

  if (checking) {
    return <div>Checking authentication...</div>;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet context={{ user }} />;
}
