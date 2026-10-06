import React from "react";
import { Link, Outlet, useLocation, useNavigate, useOutletContext } from "react-router-dom";
import { apiFetch } from "../api/apiFetch";

const backendDocsUrl =
  window.location.hostname === "localhost" ||
  window.location.hostname === "127.0.0.1"
    ? "http://localhost:8000/docs"
    : "/docs";

export default function Layout() {
  const { user } = useOutletContext();
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await apiFetch("/auth/logout", {
        method: "POST",
        credentials: "include",
      });
    } finally {
      navigate("/login", { replace: true });
    }
  };

  const isDashboard = location.pathname === "/dashboard";
  const isRegistry = location.pathname === "/" || location.pathname.startsWith("/pcbs");

  const activeStyle = {
    color: "#ffffff",
    backgroundColor: "rgba(255, 255, 255, 0.08)",
    borderBottom: "2px solid #ffffff",
    textDecoration: "none",
    fontWeight: "600",
    fontSize: "0.95rem",
    padding: "8px 14px",
    borderRadius: "6px 6px 0 0",
    transition: "all 0.2s ease"
  };

  const inactiveStyle = {
    color: "#94a3b8",
    borderBottom: "2px solid transparent",
    textDecoration: "none",
    fontWeight: "500",
    fontSize: "0.95rem",
    padding: "8px 14px",
    borderRadius: "6px 6px 0 0",
    transition: "all 0.2s ease"
  };

  return (
    <div style={{ fontFamily: "Segoe UI, Tahoma, Geneva, Verdana, sans-serif", maxWidth: "1100px", margin: "0 auto", padding: "20px" }}>
      <header
        style={{
          borderBottom: "1px solid #334155",
          paddingBottom: "15px",
          marginBottom: "30px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "15px"
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <span style={{ fontSize: "1.5rem" }}>🌱</span>
          <h2 style={{ margin: 0, color: "#4ade80", fontSize: "1.4rem", fontWeight: "700", whiteSpace: "nowrap" }}>
            GreenUp PCB LIS
          </h2>
        </div>
        <nav style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <Link
            to="/dashboard"
            style={isDashboard ? activeStyle : inactiveStyle}
          >
            📊 Dashboard
          </Link>
          <Link
            to="/"
            style={isRegistry ? activeStyle : inactiveStyle}
          >
            PCB Registry
          </Link>
          {user?.role === "admin" && (
            <>
              <Link
                to="/users"
                style={location.pathname === "/users" ? activeStyle : inactiveStyle}
              >
                👥 User Management
              </Link>

              <a
                href={backendDocsUrl}
                target="_blank"
                rel="noreferrer"
                style={inactiveStyle}
              >
                ⚙️ Backend / Swagger
              </a>
            </>
          )}

          <Link
            to="/change-password"
            style={
              location.pathname === "/change-password"
                ? activeStyle
                : inactiveStyle
            }
          >
            🔑 Change Password
          </Link>

          <Link
            to="/new"
            style={{
              padding: "8px 16px",
              background: "#16a34a",
              color: "#ffffff",
              textDecoration: "none",
              borderRadius: "6px",
              fontWeight: "600",
              fontSize: "0.95rem",
              boxShadow: "0 2px 4px rgba(0,0,0,0.15)",
              marginLeft: "12px"
            }}
          >
            + Register New PCB
          </Link>
          <button
            type="button"
            onClick={handleLogout}
            style={{
              padding: "8px 14px",
              background: "transparent",
              color: "#94a3b8",
              border: "1px solid #475569",
              borderRadius: "6px",
              fontWeight: "500",
              fontSize: "0.95rem",
              cursor: "pointer",
              marginLeft: "4px"
            }}
          >
            Logout
          </button>
        </nav>
      </header>
      <main>
        <Outlet context={{ user }} />
      </main>
    </div>
  );
}
