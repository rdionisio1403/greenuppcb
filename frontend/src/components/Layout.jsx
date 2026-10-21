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

  const [theme, setTheme] = React.useState(() => {
    const savedTheme = localStorage.getItem("greenupcb-theme");
    if (savedTheme === "light" || savedTheme === "dark") return savedTheme;
    return window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light";
  });

  React.useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("greenupcb-theme", theme);
  }, [theme]);

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
    color: "var(--nav-active-text)",
    backgroundColor: "var(--nav-active-bg)",
    borderBottom: "2px solid var(--nav-active-text)",
    textDecoration: "none",
    fontWeight: "600",
    fontSize: "0.95rem",
    padding: "8px 14px",
    borderRadius: "6px 6px 0 0",
    transition: "all 0.2s ease"
  };

  const inactiveStyle = {
    color: "var(--nav-text)",
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
          borderBottom: "1px solid var(--app-border)",
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
          <h2 style={{ margin: 0, color: "var(--app-success)", fontSize: "1.4rem", fontWeight: "700", whiteSpace: "nowrap" }}>
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
                to="/user-management"
                style={location.pathname === "/user-management" ? activeStyle : inactiveStyle}
              >
                👥 User Management
              </Link>

              <Link
                to="/customer-management"
                style={location.pathname === "/customer-management" ? activeStyle : inactiveStyle}
              >
                🏢 Customers
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
            to="/account-settings"
            style={
              ["/account-settings", "/change-password"].includes(location.pathname)
                ? activeStyle
                : inactiveStyle
            }
          >
            ⚙️ Account Settings
          </Link>

          <Link
            to="/new"
            style={{
              padding: "8px 16px",
              background: "var(--app-button-success)",
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
              color: "var(--nav-text)",
              border: "1px solid var(--app-border)",
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
      <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: "12px" }}>
        <button
          type="button"
          onClick={() => setTheme((current) => current === "dark" ? "light" : "dark")}
          aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
          style={{
            padding: "8px 12px",
            border: "1px solid var(--app-border)",
            borderRadius: "8px",
            background: "var(--app-surface)",
            color: "var(--app-text)",
            cursor: "pointer",
            fontWeight: 600
          }}
        >
          {theme === "dark" ? "☀️ Light mode" : "🌙 Dark mode"}
        </button>
      </div>
      <main>
        <Outlet context={{ user }} />
      </main>
    </div>
  );
}
