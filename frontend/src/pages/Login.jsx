import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

export default function Login() {
  const navigate = useNavigate();

  const [role, setRole] = useState("user");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [theme, setTheme] = useState(() => {
    const savedTheme = localStorage.getItem("greenupcb-theme");
    if (savedTheme === "light" || savedTheme === "dark") return savedTheme;
    return window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light";
  });

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("greenupcb-theme", theme);
  }, [theme]);

  const handleSubmit = async (e) => {
    e.preventDefault();

    setError("");
    setLoading(true);

    try {
      const response = await fetch("/auth/login", {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          username,
          password,
          role,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Login failed");
      }

      sessionStorage.setItem("csrf_token", data.csrf_token);
      navigate("/dashboard");
    } catch (err) {
      setError(err.message || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        position: "relative",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "var(--app-bg)",
        padding: "20px",
        fontFamily: "Segoe UI, Tahoma, Geneva, Verdana, sans-serif",
      }}
    >

      <div style={{ position: "absolute", top: "20px", right: "20px", display: "flex", justifyContent: "flex-end" }}>
<button
        type="button"
        onClick={() =>
          setTheme((current) => current === "dark" ? "light" : "dark")
        }
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

<div
        style={{
          width: "100%",
          maxWidth: "420px",
          background: "var(--app-surface)",
          padding: "35px",
          borderRadius: "12px",
          boxShadow: "var(--app-shadow)",
          border: "1px solid var(--app-border)",
        }}
      >
        <div style={{ textAlign: "center", marginBottom: "30px" }}>
          <div style={{ fontSize: "2.5rem", marginBottom: "10px" }}>🌱</div>

<h1
            style={{
              margin: 0,
              color: "var(--app-success)",
              fontSize: "1.8rem",
            }}
          >
            GreenUp PCB LIS
          </h1>

          <p
            style={{
              color: "var(--app-text-muted)",
              marginTop: "8px",
              marginBottom: "20px",
            }}
          >
            Sign in to continue
          </p>

          <div
            style={{
              display: "flex",
              gap: "8px",
              background: "var(--app-surface-muted)",
              padding: "5px",
              borderRadius: "8px",
            }}
          >
            <button
              type="button"
              onClick={() => {
                setRole("user");
                setError("");
              }}
              style={{
                flex: 1,
                padding: "10px",
                border: "none",
                borderRadius: "6px",
                background: role === "user" ? "var(--app-button-success)" : "transparent",
                color: (role === "user" ? "#ffffff" : "var(--app-text)"),
                fontWeight: "600",
                cursor: "pointer",
              }}
            >
              User Login
            </button>

            <button
              type="button"
              onClick={() => {
                setRole("admin");
                setError("");
              }}
              style={{
                flex: 1,
                padding: "10px",
                border: "none",
                borderRadius: "6px",
                background: role === "admin" ? "var(--app-button-success)" : "transparent",
                color: (role === "admin" ? "#ffffff" : "var(--app-text)"),
                fontWeight: "600",
                cursor: "pointer",
              }}
            >
              Admin Login
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: "18px" }}>
            <label
              style={{
                display: "block",
                color: "var(--app-text)",
                marginBottom: "7px",
                fontWeight: "600",
              }}
            >
              Username
            </label>

            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              autoComplete="username"
              style={{
                width: "100%",
                boxSizing: "border-box",
                padding: "11px 12px",
                borderRadius: "6px",
                border: "1px solid var(--app-border)",
                background: "var(--app-input-bg)",
                color: "var(--app-text)",
                fontSize: "1rem",
              }}
            />
          </div>

          <div style={{ marginBottom: "20px" }}>
            <label
              style={{
                display: "block",
                color: "var(--app-text)",
                marginBottom: "7px",
                fontWeight: "600",
              }}
            >
              Password
            </label>

            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
              style={{
                width: "100%",
                boxSizing: "border-box",
                padding: "11px 12px",
                borderRadius: "6px",
                border: "1px solid var(--app-border)",
                background: "var(--app-input-bg)",
                color: "var(--app-text)",
                fontSize: "1rem",
              }}
            />
          </div>

          {error && (
            <div
              style={{
                marginBottom: "18px",
                padding: "10px 12px",
                borderRadius: "6px",
                background: "rgba(239, 68, 68, 0.12)",
                border: "1px solid var(--app-error-border)",
                color: "var(--app-error-text)",
              }}
            >
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              width: "100%",
              padding: "12px",
              border: "none",
              borderRadius: "6px",
              background: loading ? "#166534" : "var(--app-button-success)",
              color: "#ffffff",
              fontSize: "1rem",
              fontWeight: "600",
              cursor: loading ? "not-allowed" : "pointer",
            }}
          >
            {loading
              ? "Signing in..."
              : role === "admin"
                ? "Sign In as Admin"
                : "Sign In"}
          </button>
        </form>
        <div style={{ textAlign: "center", marginTop: "18px" }}>
          <button
            type="button"
            onClick={() => navigate("/forgot-password")}
            style={{
              background: "transparent",
              border: "none",
              color: "var(--app-success)",
              cursor: "pointer",
              fontSize: "0.95rem",
              textDecoration: "underline",
            }}
          >
            Forgot your password?
          </button>
        </div>
      </div>
    </div>
  );
}
