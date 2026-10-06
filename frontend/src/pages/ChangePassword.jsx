import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiFetch } from "../api/apiFetch";

export default function ChangePassword() {
  const navigate = useNavigate();

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const handleSubmit = async (event) => {
    event.preventDefault();

    setError("");
    setSuccess("");

    if (newPassword !== confirmPassword) {
      setError("New passwords do not match.");
      return;
    }

    if (currentPassword === newPassword) {
      setError("New password must be different from the current password.");
      return;
    }

    setLoading(true);

    try {
      const response = await apiFetch("/auth/change-password", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
          confirm_password: confirmPassword,
        }),
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error("Your session has expired. Please log in again.");
        }

        if (response.status === 403) {
          throw new Error(
            data.detail || "Security validation failed. Please log in again."
          );
        }

        if (response.status === 422) {
          const validationMessage = Array.isArray(data.detail)
            ? data.detail
                .map((item) => item.msg)
                .filter(Boolean)
                .join(" ")
            : data.detail;

          throw new Error(
            validationMessage || "Please check the password fields."
          );
        }

        throw new Error(data.detail || "Failed to change password.");
      }

      setSuccess(
        data.message ||
          "Password changed successfully. Please log in again."
      );

      sessionStorage.removeItem("csrf_token");

      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");

      setTimeout(() => {
        navigate("/login", { replace: true });
      }, 1500);
    } catch (err) {
      setError(err.message || "Failed to change password.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        maxWidth: "520px",
        margin: "20px auto",
        padding: "30px",
        background: "#1e293b",
        border: "1px solid #334155",
        borderRadius: "10px",
        boxShadow: "0 8px 24px rgba(0,0,0,0.25)",
      }}
    >
      <div style={{ marginBottom: "25px" }}>
        <h1
          style={{
            margin: 0,
            color: "#e2e8f0",
            fontSize: "1.7rem",
          }}
        >
          Change Password
        </h1>

        <p
          style={{
            color: "#94a3b8",
            marginTop: "8px",
            lineHeight: "1.5",
          }}
        >
          Update your account password. For security, all active sessions will
          be signed out after the password is changed.
        </p>
      </div>

      {error && (
        <div
          role="alert"
          style={{
            marginBottom: "20px",
            padding: "12px",
            borderRadius: "6px",
            background: "rgba(239, 68, 68, 0.12)",
            border: "1px solid rgba(239, 68, 68, 0.4)",
            color: "#fca5a5",
          }}
        >
          {error}
        </div>
      )}

      {success && (
        <div
          role="status"
          style={{
            marginBottom: "20px",
            padding: "12px",
            borderRadius: "6px",
            background: "rgba(34, 197, 94, 0.12)",
            border: "1px solid rgba(34, 197, 94, 0.4)",
            color: "#86efac",
          }}
        >
          {success}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <label
          htmlFor="current-password"
          style={{
            display: "block",
            marginBottom: "7px",
            color: "#cbd5e1",
            fontWeight: "600",
          }}
        >
          Current Password
        </label>

        <input
          id="current-password"
          type="password"
          value={currentPassword}
          onChange={(event) => setCurrentPassword(event.target.value)}
          autoComplete="current-password"
          required
          disabled={loading}
          style={inputStyle}
        />

        <label
          htmlFor="new-password"
          style={{
            display: "block",
            marginTop: "18px",
            marginBottom: "7px",
            color: "#cbd5e1",
            fontWeight: "600",
          }}
        >
          New Password
        </label>

        <input
          id="new-password"
          type="password"
          value={newPassword}
          onChange={(event) => setNewPassword(event.target.value)}
          autoComplete="new-password"
          minLength={12}
          maxLength={128}
          required
          disabled={loading}
          style={inputStyle}
        />

        <p
          style={{
            margin: "6px 0 0",
            color: "#64748b",
            fontSize: "0.85rem",
          }}
        >
          Minimum 12 characters.
        </p>

        <label
          htmlFor="confirm-password"
          style={{
            display: "block",
            marginTop: "18px",
            marginBottom: "7px",
            color: "#cbd5e1",
            fontWeight: "600",
          }}
        >
          Confirm New Password
        </label>

        <input
          id="confirm-password"
          type="password"
          value={confirmPassword}
          onChange={(event) => setConfirmPassword(event.target.value)}
          autoComplete="new-password"
          minLength={12}
          maxLength={128}
          required
          disabled={loading}
          style={inputStyle}
        />

        <div
          style={{
            display: "flex",
            gap: "10px",
            marginTop: "25px",
          }}
        >
          <button
            type="submit"
            disabled={loading}
            style={{
              flex: 1,
              padding: "11px 16px",
              background: loading ? "#166534" : "#16a34a",
              color: "#ffffff",
              border: "none",
              borderRadius: "6px",
              fontWeight: "600",
              fontSize: "0.95rem",
              cursor: loading ? "not-allowed" : "pointer",
            }}
          >
            {loading ? "Changing Password..." : "Change Password"}
          </button>

          <button
            type="button"
            onClick={() => navigate(-1)}
            disabled={loading}
            style={{
              padding: "11px 16px",
              background: "#334155",
              color: "#ffffff",
              border: "1px solid #475569",
              borderRadius: "6px",
              fontWeight: "500",
              fontSize: "0.95rem",
              cursor: loading ? "not-allowed" : "pointer",
            }}
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}

const inputStyle = {
  width: "100%",
  boxSizing: "border-box",
  padding: "11px 12px",
  background: "#0f172a",
  color: "#f8fafc",
  border: "1px solid #475569",
  borderRadius: "6px",
  fontSize: "0.95rem",
  outline: "none",
};
