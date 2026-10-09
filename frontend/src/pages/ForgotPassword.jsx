import { useState } from "react";
import { Link } from "react-router-dom";

const cardStyle = {
  width: "100%",
  maxWidth: "420px",
  boxSizing: "border-box",
  background: "#1e293b",
  padding: "35px",
  borderRadius: "12px",
  boxShadow: "0 10px 30px rgba(0,0,0,0.3)",
};

const inputStyle = {
  width: "100%",
  boxSizing: "border-box",
  padding: "11px 12px",
  borderRadius: "6px",
  border: "1px solid #475569",
  background: "#0f172a",
  color: "#ffffff",
  fontSize: "1rem",
};

const buttonStyle = {
  width: "100%",
  padding: "12px",
  border: "none",
  borderRadius: "6px",
  background: "#16a34a",
  color: "#ffffff",
  fontSize: "1rem",
  fontWeight: "600",
  cursor: "pointer",
};

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setMessage("");
    setError("");
    setLoading(true);

    try {
      const response = await fetch("/auth/password-reset/request", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });

      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data.detail || "Unable to submit the request.");
      }

      setMessage(
        "The request endpoint responded, but email delivery is not configured yet. No reset email has been sent."
      );
    } catch (err) {
      setError(err.message || "Unable to submit the request.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main style={{
      minHeight: "100vh",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      background: "#0f172a",
      padding: "20px",
      boxSizing: "border-box",
      fontFamily: "Segoe UI, Tahoma, Geneva, Verdana, sans-serif",
    }}>
      <section style={cardStyle}>
        <header style={{ textAlign: "center", marginBottom: "28px" }}>
          <div style={{ fontSize: "2.5rem", marginBottom: "10px" }}>🌱</div>
          <h1 style={{ margin: 0, color: "#4ade80", fontSize: "1.8rem" }}>
            GreenUp PCB LIS
          </h1>
          <h2 style={{ color: "#e2e8f0", fontSize: "1.2rem", marginTop: "22px" }}>
            Reset your password
          </h2>
          <p style={{ color: "#94a3b8", marginTop: "8px" }}>
            Enter the email address associated with your account.
          </p>
        </header>

        <form onSubmit={handleSubmit}>
          <label htmlFor="reset-email" style={{
            display: "block",
            color: "#e2e8f0",
            marginBottom: "7px",
            fontWeight: "600",
          }}>
            Email address
          </label>
          <input
            id="reset-email"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            autoComplete="email"
            required
            maxLength={254}
            style={{ ...inputStyle, marginBottom: "18px" }}
          />

          {message && (
            <p role="status" style={{
              color: "#fde68a",
              background: "rgba(234,179,8,0.12)",
              padding: "12px",
              borderRadius: "6px",
              marginBottom: "18px",
            }}>
              {message}
            </p>
          )}

          {error && (
            <p role="alert" style={{
              color: "#fca5a5",
              background: "rgba(239,68,68,0.12)",
              padding: "12px",
              borderRadius: "6px",
              marginBottom: "18px",
            }}>
              {error}
            </p>
          )}

          <button type="submit" disabled={loading} style={{
            ...buttonStyle,
            opacity: loading ? 0.7 : 1,
            cursor: loading ? "not-allowed" : "pointer",
          }}>
            {loading ? "Submitting..." : "Submit request"}
          </button>
        </form>

        <p style={{ textAlign: "center", marginTop: "22px" }}>
          <Link to="/login" style={{ color: "#86efac" }}>
            Back to sign in
          </Link>
        </p>
      </section>
    </main>
  );
}
