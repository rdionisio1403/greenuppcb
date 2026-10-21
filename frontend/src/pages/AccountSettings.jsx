import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiFetch } from "../api/apiFetch";

const inputStyle = {
  width: "100%",
  boxSizing: "border-box",
  padding: "11px 12px",
  background: "var(--app-input-bg)",
  color: "var(--app-text)",
  border: "1px solid var(--app-border)",
  borderRadius: "6px",
  fontSize: "0.95rem",
  outline: "none",
};

const labelStyle = {
  display: "block",
  marginBottom: "7px",
  color: "var(--app-text)",
  fontWeight: "600",
};

const cardStyle = {
  padding: "24px",
  background: "var(--app-surface)",
  border: "1px solid var(--app-surface-muted)",
  borderRadius: "10px",
  boxShadow: "0 8px 24px rgba(0,0,0,0.12)",
  marginBottom: "24px",
};

const primaryButtonStyle = {
  padding: "11px 16px",
  background: "var(--app-button-success)",
  color: "#ffffff",
  border: "none",
  borderRadius: "6px",
  fontWeight: "600",
  fontSize: "0.95rem",
  cursor: "pointer",
};

async function readJson(response) {
  return response.json().catch(() => ({}));
}

function getErrorMessage(data, fallback) {
  if (Array.isArray(data.detail)) {
    return data.detail.map((item) => item.msg).filter(Boolean).join(" ");
  }
  return data.detail || fallback;
}

function Feedback({ message, type = "error" }) {
  if (!message) return null;

  const isSuccess = type === "success";

  return (
    <div
      role={isSuccess ? "status" : "alert"}
      style={{
        marginBottom: "18px",
        padding: "12px",
        borderRadius: "6px",
        background: isSuccess
          ? "rgba(34, 197, 94, 0.12)"
          : "rgba(239, 68, 68, 0.12)",
        border: `1px solid ${
          isSuccess
            ? "rgba(34, 197, 94, 0.4)"
            : "rgba(239, 68, 68, 0.4)"
        }`,
        color: isSuccess ? "var(--app-success)" : "var(--app-error-text)",
      }}
    >
      {message}
    </div>
  );
}

export default function AccountSettings() {
  const navigate = useNavigate();

  const [profile, setProfile] = useState({ username: "", email: "" });
  const [loadingProfile, setLoadingProfile] = useState(true);
  const [profilePassword, setProfilePassword] = useState("");
  const [savingProfile, setSavingProfile] = useState(false);
  const [profileError, setProfileError] = useState("");
  const [profileSuccess, setProfileSuccess] = useState("");

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [changingPassword, setChangingPassword] = useState(false);
  const [passwordError, setPasswordError] = useState("");
  const [passwordSuccess, setPasswordSuccess] = useState("");
  const [showDeletionModal, setShowDeletionModal] = useState(false);
  const [deletionPassword, setDeletionPassword] = useState("");
  const [deletingAccount, setDeletingAccount] = useState(false);
  const [deletionError, setDeletionError] = useState("");
  const [deletionSuccess, setDeletionSuccess] = useState("");


  useEffect(() => {
    let active = true;

    async function loadProfile() {
      try {
        const response = await apiFetch("/auth/me");

        if (response.status === 401) {
          navigate("/login", { replace: true });
          return;
        }

        const data = await readJson(response);
        if (!response.ok) {
          throw new Error(getErrorMessage(data, "Could not load account details."));
        }

        if (active) {
          setProfile({
            username: data.username || "",
            email: data.email || "",
          });
        }
      } catch (error) {
        if (active) {
          setProfileError(error.message || "Could not load account details.");
        }
      } finally {
        if (active) setLoadingProfile(false);
      }
    }

    loadProfile();
    return () => {
      active = false;
    };
  }, [navigate]);

  const handleProfileSubmit = async (event) => {
    event.preventDefault();
    setProfileError("");
    setProfileSuccess("");

    const username = profile.username.trim();
    const email = profile.email.trim();

    if (!username) {
      setProfileError("Username cannot be empty.");
      return;
    }

    setSavingProfile(true);

    try {
      const response = await apiFetch("/auth/update-profile", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username,
          email: email || null,
          current_password: profilePassword,
        }),
      });

      const data = await readJson(response);

      if (!response.ok) {
        if (response.status === 401) {
          navigate("/login", { replace: true });
          return;
        }
        throw new Error(
          getErrorMessage(data, "Failed to update account information.")
        );
      }

      setProfile({
        username: data.username || "",
        email: data.email || "",
      });
      setProfilePassword("");
      setProfileSuccess("Account information updated successfully.");
    } catch (error) {
      setProfileError(error.message || "Failed to update account information.");
    } finally {
      setSavingProfile(false);
    }
  };

  const handlePasswordSubmit = async (event) => {
    event.preventDefault();
    setPasswordError("");
    setPasswordSuccess("");

    if (newPassword !== confirmPassword) {
      setPasswordError("New passwords do not match.");
      return;
    }

    if (currentPassword === newPassword) {
      setPasswordError("New password must be different from the current password.");
      return;
    }

    setChangingPassword(true);

    try {
      const response = await apiFetch("/auth/change-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
          confirm_password: confirmPassword,
        }),
      });

      const data = await readJson(response);

      if (!response.ok) {
        if (response.status === 401) {
          navigate("/login", { replace: true });
          return;
        }
        throw new Error(getErrorMessage(data, "Failed to change password."));
      }

      setPasswordSuccess(
        data.message || "Password changed successfully. Please log in again."
      );
      sessionStorage.removeItem("csrf_token");

      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");

      window.setTimeout(() => {
        navigate("/login", { replace: true });
      }, 1500);
    } catch (error) {
      setPasswordError(error.message || "Failed to change password.");
    } finally {
      setChangingPassword(false);
    }
  };


  const handleRequestAccountDeletion = async (event) => {
    event.preventDefault();
    setDeletionError("");
    setDeletingAccount(true);

    try {
      const response = await apiFetch("/auth/request-account-deletion", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ current_password: deletionPassword }),
      });

      const data = await readJson(response);

      if (!response.ok) {
        if (response.status === 401) {
          navigate("/login", { replace: true });
          return;
        }
        throw new Error(
          getErrorMessage(data, "Unable to schedule account deletion.")
        );
      }

      setShowDeletionModal(false);
      setDeletionPassword("");
      setDeletionSuccess(
        data.message ||
          "Account deletion is scheduled. Sign in within 30 days to cancel."
      );
      sessionStorage.removeItem("csrf_token");

      window.setTimeout(() => {
        navigate("/login", { replace: true });
      }, 2200);
    } catch (error) {
      setDeletionError(
        error.message || "Unable to schedule account deletion."
      );
    } finally {
      setDeletingAccount(false);
    }
  };

  return (
    <main style={{ maxWidth: "760px", margin: "20px auto", color: "var(--app-text)" }}>
      <header style={{ marginBottom: "25px" }}>
        <h1 style={{ margin: 0, fontSize: "1.8rem" }}>Account Settings</h1>
        <p style={{ color: "var(--app-text-muted)", lineHeight: "1.6" }}>
          Manage your account information and security preferences.
        </p>
      </header>

      {loadingProfile ? (
        <p style={{ color: "var(--app-text-muted)" }}>Loading account details...</p>
      ) : (
        <section style={cardStyle}>
          <h2 style={{ marginTop: 0, fontSize: "1.25rem" }}>Profile Information</h2>
          <p style={{ color: "var(--app-text-muted)", lineHeight: "1.5" }}>
            Update your username or email address. Your current password is
            required to save changes. Leave the email field empty if you do not
            use an email address for this account.
          </p>

          <Feedback message={profileError} />
          <Feedback message={profileSuccess} type="success" />

          <form onSubmit={handleProfileSubmit}>
            <label htmlFor="account-username" style={labelStyle}>Username</label>
            <input
              id="account-username"
              type="text"
              value={profile.username}
              onChange={(event) =>
                setProfile((previous) => ({ ...previous, username: event.target.value }))
              }
              autoComplete="username"
              minLength={1}
              maxLength={100}
              required
              disabled={savingProfile}
              style={inputStyle}
            />

            <label htmlFor="account-email" style={{ ...labelStyle, marginTop: "18px" }}>
              Email Address (optional)
            </label>
            <input
              id="account-email"
              type="email"
              value={profile.email}
              onChange={(event) =>
                setProfile((previous) => ({ ...previous, email: event.target.value }))
              }
              autoComplete="email"
              maxLength={200}
              disabled={savingProfile}
              style={inputStyle}
            />

            <label htmlFor="profile-current-password" style={{ ...labelStyle, marginTop: "18px" }}>
              Confirm with Current Password
            </label>
            <input
              id="profile-current-password"
              type="password"
              value={profilePassword}
              onChange={(event) => setProfilePassword(event.target.value)}
              autoComplete="current-password"
              required
              disabled={savingProfile}
              style={inputStyle}
            />

            <button
              type="submit"
              disabled={savingProfile || loadingProfile}
              style={{
                ...primaryButtonStyle,
                marginTop: "22px",
                opacity: savingProfile ? 0.7 : 1,
                cursor: savingProfile ? "not-allowed" : "pointer",
              }}
            >
              {savingProfile ? "Saving Changes..." : "Save Profile"}
            </button>
          </form>
        </section>
      )}

      <section style={cardStyle}>
        <h2 style={{ marginTop: 0, fontSize: "1.25rem" }}>Change Password</h2>
        <p style={{ color: "var(--app-text-muted)", lineHeight: "1.5" }}>
          Choose a new password with at least 12 characters. For security,
          changing your password signs out all active sessions.
        </p>

        <Feedback message={passwordError} />
        <Feedback message={passwordSuccess} type="success" />

        <form onSubmit={handlePasswordSubmit}>
          <label htmlFor="current-password" style={labelStyle}>Current Password</label>
          <input
            id="current-password"
            type="password"
            value={currentPassword}
            onChange={(event) => setCurrentPassword(event.target.value)}
            autoComplete="current-password"
            required
            disabled={changingPassword}
            style={inputStyle}
          />

          <label htmlFor="new-password" style={{ ...labelStyle, marginTop: "18px" }}>
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
            disabled={changingPassword}
            style={inputStyle}
          />
          <p style={{ margin: "6px 0 0", color: "var(--app-text-muted)", fontSize: "0.85rem" }}>
            Minimum 12 characters.
          </p>

          <label htmlFor="confirm-password" style={{ ...labelStyle, marginTop: "18px" }}>
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
            disabled={changingPassword}
            style={inputStyle}
          />

          <button
            type="submit"
            disabled={changingPassword}
            style={{
              ...primaryButtonStyle,
              marginTop: "22px",
              opacity: changingPassword ? 0.7 : 1,
              cursor: changingPassword ? "not-allowed" : "pointer",
            }}
          >
            {changingPassword ? "Changing Password..." : "Update Password"}
          </button>
        </form>
      </section>

      <section
        style={{
          ...cardStyle,
          border: "1px solid var(--app-error-border)",
        }}
      >
        <h2 style={{
          marginTop: 0,
          fontSize: "1.25rem",
          color: "var(--app-error-text)",
        }}>
          Delete Account
        </h2>
        <p style={{ color: "var(--app-text-muted)", lineHeight: "1.6" }}>
          Deletion has a 30-day grace period. Signing in successfully during
          that period cancels the request. After the period expires, the
          account is permanently deleted. PCB, customer and audit history
          are retained where possible, with account ownership references removed.
        </p>

        <Feedback message={deletionSuccess} type="success" />

        <button
          type="button"
          disabled={Boolean(deletionSuccess)}
          onClick={() => {
            setDeletionError("");
            setDeletionPassword("");
            setShowDeletionModal(true);
          }}
          style={{
            ...primaryButtonStyle,
            background: "#b91c1c",
            marginTop: "8px",
            opacity: deletionSuccess ? 0.6 : 1,
          }}
        >
          Delete Account
        </button>
      </section>

      {showDeletionModal && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            zIndex: 2000,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "20px",
            boxSizing: "border-box",
            background: "rgba(0, 0, 0, 0.65)",
          }}
        >
          <section
            role="dialog"
            aria-modal="true"
            aria-labelledby="delete-account-title"
            style={{
              width: "100%",
              maxWidth: "480px",
              boxSizing: "border-box",
              padding: "26px",
              borderRadius: "12px",
              background: "var(--app-surface)",
              color: "var(--app-text)",
              border: "1px solid var(--app-error-border)",
              boxShadow: "0 20px 60px rgba(0,0,0,0.35)",
            }}
          >
            <h2
              id="delete-account-title"
              style={{ marginTop: 0, color: "var(--app-error-text)" }}
            >
              Are you sure?
            </h2>
            <p style={{ color: "var(--app-text-muted)", lineHeight: "1.6" }}>
              Your account will be scheduled for permanent deletion in 30 days.
              You will be signed out. Successfully signing in during those 30
              days cancels the request.
            </p>
            <p style={{ fontWeight: "600" }}>
              Enter your current password to confirm.
            </p>

            <Feedback message={deletionError} />

            <form onSubmit={handleRequestAccountDeletion}>
              <label htmlFor="delete-account-password" style={labelStyle}>
                Current Password
              </label>
              <input
                id="delete-account-password"
                type="password"
                value={deletionPassword}
                onChange={(event) => setDeletionPassword(event.target.value)}
                autoComplete="current-password"
                required
                disabled={deletingAccount}
                style={inputStyle}
              />

              <div style={{
                display: "flex",
                justifyContent: "flex-end",
                gap: "10px",
                flexWrap: "wrap",
                marginTop: "24px",
              }}>
                <button
                  type="button"
                  disabled={deletingAccount}
                  onClick={() => {
                    setShowDeletionModal(false);
                    setDeletionPassword("");
                    setDeletionError("");
                  }}
                  style={{
                    padding: "11px 16px",
                    background: "var(--app-surface-muted)",
                    color: "var(--app-text)",
                    border: "1px solid var(--app-border)",
                    borderRadius: "6px",
                    fontWeight: "600",
                    cursor: "pointer",
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={deletingAccount || !deletionPassword}
                  style={{
                    padding: "11px 16px",
                    background: "#b91c1c",
                    color: "#ffffff",
                    border: "none",
                    borderRadius: "6px",
                    fontWeight: "600",
                    cursor: deletingAccount ? "not-allowed" : "pointer",
                    opacity: deletingAccount ? 0.7 : 1,
                  }}
                >
                  {deletingAccount ? "Scheduling..." : "Confirm Deletion"}
                </button>
              </div>
            </form>
          </section>
        </div>
      )}

    </main>
  );
}
