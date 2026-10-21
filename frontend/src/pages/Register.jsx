import { useState } from "react";
import { Link } from "react-router-dom";
import ThemeToggle from "../components/ThemeToggle";

const inputStyle = {
  width: "100%",
  boxSizing: "border-box",
  padding: "11px 12px",
  borderRadius: "6px",
  border: "1px solid var(--app-border)",
  background: "var(--app-input-bg)",
  color: "var(--app-text)",
  fontSize: "1rem",
};

const labelStyle = {
  display: "block",
  color: "var(--app-text)",
  marginBottom: "7px",
  fontWeight: "600",
};

function responseMessage(data, fallback) {
  if (Array.isArray(data.detail)) {
    return data.detail.map((item) => item.msg).filter(Boolean).join(" ");
  }

  return data.detail || fallback;
}

export default function Register() {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [registeredUsername, setRegisteredUsername] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");

    const cleanUsername = username.trim();
    const cleanEmail = email.trim().toLowerCase();

    if (!cleanUsername) {
      setError("Please enter a username.");
      return;
    }

    if (password !== confirmPassword) {
      setError("The passwords do not match.");
      return;
    }

    if (password.length < 12) {
      setError("Your password must be at least 12 characters long.");
      return;
    }

    setLoading(true);

    try {
      const response = await fetch("/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: cleanUsername,
          email: cleanEmail,
          password,
        }),
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(
          responseMessage(data, "Unable to create your account.")
        );
      }

      setRegisteredUsername(cleanUsername);
      setPassword("");
      setConfirmPassword("");
    } catch (err) {
      setError(err.message || "Unable to create your account.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main
      style={{
        minHeight: "100vh",
        position: "relative",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "var(--app-bg)",
        padding: "70px 20px 30px",
        boxSizing: "border-box",
        fontFamily: "Segoe UI, Tahoma, Geneva, Verdana, sans-serif",
      }}
    >
      <ThemeToggle />

      <section
        style={{
          width: "100%",
          maxWidth: "440px",
          boxSizing: "border-box",
          background: "var(--app-surface)",
          padding: "32px",
          borderRadius: "12px",
          boxShadow: "var(--app-shadow)",
          border: "1px solid var(--app-border)",
        }}
      >
        <header style={{ textAlign: "center", marginBottom: "26px" }}>
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
          <h2
            style={{
              color: "var(--app-text)",
              fontSize: "1.2rem",
              marginTop: "18px",
            }}
          >
            Create Account
          </h2>
          <p style={{ color: "var(--app-text-muted)", lineHeight: "1.5" }}>
            Register a new account to access the PCB registry.
          </p>
        </header>

        {registeredUsername ? (
          <div>
            <div
              role="status"
              style={{
                padding: "14px",
                borderRadius: "6px",
                background: "rgba(34, 197, 94, 0.12)",
                border: "1px solid rgba(34, 197, 94, 0.4)",
                color: "var(--app-success)",
                lineHeight: "1.5",
                marginBottom: "20px",
              }}
            >
              Account created successfully for{" "}
              <strong>{registeredUsername}</strong>. You can now sign in.
            </div>

            <Link
              to="/login"
              style={{
                display: "block",
                boxSizing: "border-box",
                width: "100%",
                padding: "12px",
                borderRadius: "6px",
                background: "var(--app-button-success)",
                color: "#ffffff",
                textDecoration: "none",
                textAlign: "center",
                fontWeight: "600",
              }}
            >
              Go to Sign In
            </Link>
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            <label htmlFor="register-username" style={labelStyle}>
              Username
            </label>
            <input
              id="register-username"
              type="text"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              autoComplete="username"
              minLength={1}
              maxLength={100}
              required
              disabled={loading}
              style={{ ...inputStyle, marginBottom: "18px" }}
            />

            <label htmlFor="register-email" style={labelStyle}>
              Email Address
            </label>
            <input
              id="register-email"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              autoComplete="email"
              maxLength={254}
              required
              disabled={loading}
              style={{ ...inputStyle, marginBottom: "18px" }}
            />

            <label htmlFor="register-password" style={labelStyle}>
              Password
            </label>
            <input
              id="register-password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete="new-password"
              minLength={12}
              maxLength={128}
              required
              disabled={loading}
              style={{ ...inputStyle, marginBottom: "7px" }}
            />
            <p
              style={{
                color: "var(--app-text-muted)",
                fontSize: "0.85rem",
                margin: "0 0 18px",
              }}
            >
              Minimum 12 characters.
            </p>

            <label htmlFor="register-confirm-password" style={labelStyle}>
              Confirm Password
            </label>
            <input
              id="register-confirm-password"
              type="password"
              value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.target.value)}
              autoComplete="new-password"
              minLength={12}
              maxLength={128}
              required
              disabled={loading}
              style={{ ...inputStyle, marginBottom: "18px" }}
            />

            {error && (
              <div
                role="alert"
                style={{
                  padding: "12px",
                  borderRadius: "6px",
                  background: "rgba(239, 68, 68, 0.12)",
                  border: "1px solid var(--app-error-border)",
                  color: "var(--app-error-text)",
                  marginBottom: "18px",
                  lineHeight: "1.5",
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
                background: "var(--app-button-success)",
                color: "#ffffff",
                fontSize: "1rem",
                fontWeight: "600",
                cursor: loading ? "not-allowed" : "pointer",
                opacity: loading ? 0.7 : 1,
              }}
            >
              {loading ? "Creating Account..." : "Create Account"}
            </button>
          </form>
        )}

        <p
          style={{
            textAlign: "center",
            marginTop: "22px",
            color: "var(--app-text-muted)",
          }}
        >
          Already have an account?{" "}
          <Link to="/login" style={{ color: "var(--app-success)" }}>
            Sign in
          </Link>
        </p>
      </section>
    </main>
  );
}
