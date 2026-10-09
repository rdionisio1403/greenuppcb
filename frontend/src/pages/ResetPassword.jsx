import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

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

export default function ResetPassword() {
  const [searchParams] = useSearchParams();
  const [token, setToken] = useState(searchParams.get("token") || "");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setMessage("");
    setError("");

    if (newPassword !== confirmPassword) {
      setError("The passwords do not match.");
      return;
    }

    setLoading(true);
    try {
      const response = await fetch("/auth/password-reset/confirm", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          token,
          new_password: newPassword,
          confirm_password: confirmPassword,
        }),
      });

      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data.detail || "Unable to reset the password.");
      }

      setMessage(data.message || "Password reset successful. Please sign in.");
      setToken("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err) {
      setError(err.message || "Unable to reset the password.");
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
      <section style={{
        width: "100%",
        maxWidth: "420px",
        boxSizing: "border-box",
        background: "#1e293b",
        padding: "35px",
        borderRadius: "12px",
        boxShadow: "0 10px 30px rgba(0,0,0,0.3)",
      }}>
        <header style={{ textAlign: "center", marginBottom: "28px" }}>
          <div style={{ fontSize: "2.5rem", marginBottom: "10px" }}>🌱</div>
          <h1 style={{ margin: 0, color: "#4ade80", fontSize: "1.8rem" }}>
            GreenUp PCB LIS
          </h1>
          <h2 style={{ color: "#e2e8f0", fontSize: "1.2rem", marginTop: "22px" }}>
            Choose a new password
          </h2>
        </header>

        <form onSubmit={handleSubmit}>
          <label htmlFor="reset-token" style={{
            display: "block", color: "#e2e8f0", marginBottom: "7px", fontWeight: "600",
          }}>
            Reset token
          </label>
          <input
            id="reset-token"
            type="password"
            value={token}
            onChange={(event) => setToken(event.target.value)}
            autoComplete="off"
            required
            minLength={20}
            maxLength={256}
            style={{ ...inputStyle, marginBottom: "18px" }}
          />

          <label htmlFor="new-password" style={{
            display: "block", color: "#e2e8f0", marginBottom: "7px", fontWeight: "600",
          }}>
            New password
          </label>
          <input
            id="new-password"
            type="password"
            value={newPassword}
            onChange={(event) => setNewPassword(event.target.value)}
            autoComplete="new-password"
            required
            minLength={12}
            maxLength={128}
            style={{ ...inputStyle, marginBottom: "18px" }}
          />

          <label htmlFor="confirm-password" style={{
            display: "block", color: "#e2e8f0", marginBottom: "7px", fontWeight: "600",
          }}>
            Confirm new password
          </label>
          <input
            id="confirm-password"
            type="password"
            value={confirmPassword}
            onChange={(event) => setConfirmPassword(event.target.value)}
            autoComplete="new-password"
            required
            minLength={12}
            maxLength={128}
            style={{ ...inputStyle, marginBottom: "18px" }}
          />

          {message && (
            <p role="status" style={{
              color: "#86efac",
              background: "rgba(22,163,74,0.12)",
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
            width: "100%",
            padding: "12px",
            border: "none",
            borderRadius: "6px",
            background: "#16a34a",
            color: "#ffffff",
            fontSize: "1rem",
            fontWeight: "600",
            cursor: loading ? "not-allowed" : "pointer",
            opacity: loading ? 0.7 : 1,
          }}>
            {loading ? "Updating..." : "Update password"}
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
