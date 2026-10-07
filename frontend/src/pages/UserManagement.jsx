import React, { useEffect, useState } from "react";
import { apiFetch } from "../api/apiFetch";
import { Navigate, useOutletContext } from "react-router-dom";

export default function UserManagement() {
  const { user: currentUser } = useOutletContext();

  const [users, setUsers] = useState([]);
  const [sessions, setSessions] = useState({});
  const [expandedUserId, setExpandedUserId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(null);
  const [error, setError] = useState("");

  const loadUsers = async () => {
    setError("");

    try {
      const response = await apiFetch("/users");

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || "Failed to load users");
      }

      const data = await response.json();
      setUsers(data);
    } catch (err) {
      setError(err.message || "Failed to load users");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUsers();
  }, []);

  if (currentUser?.role !== "admin") {
    return <Navigate to="/dashboard" replace />;
  }

  const handleDisable = async (userId) => {
    if (!window.confirm("Are you sure you want to disable this user?")) {
      return;
    }

    setActionLoading(`disable-${userId}`);
    setError("");

    try {
      const response = await apiFetch(`/users/${userId}/disable`, {
        method: "PATCH",
      });

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || "Failed to disable user");
      }

      await loadUsers();
    } catch (err) {
      setError(err.message || "Failed to disable user");
    } finally {
      setActionLoading(null);
    }
  };

  const loadSessions = async (userId) => {
    if (expandedUserId === userId) {
      setExpandedUserId(null);
      return;
    }

    setActionLoading(`sessions-${userId}`);
    setError("");

    try {
      const response = await apiFetch(`/users/${userId}/sessions`);

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || "Failed to load sessions");
      }

      const data = await response.json();

      setSessions((prev) => ({
        ...prev,
        [userId]: data,
      }));

      setExpandedUserId(userId);
    } catch (err) {
      setError(err.message || "Failed to load sessions");
    } finally {
      setActionLoading(null);
    }
  };

  const handleRevokeSession = async (userId, sessionId) => {
    if (!window.confirm("Revoke this session?")) {
      return;
    }

    setActionLoading(`revoke-${sessionId}`);
    setError("");

    try {
      const response = await apiFetch(
        `/users/${userId}/sessions/${sessionId}`,
        {
          method: "DELETE",
        }
      );

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || "Failed to revoke session");
      }

      setSessions((prev) => ({
        ...prev,
        [userId]: (prev[userId] || []).filter(
          (session) => session.id !== sessionId
        ),
      }));

    } catch (err) {
      setError(err.message || "Failed to revoke session");
    } finally {
      setActionLoading(null);
    }
  };

  const handleRevokeAll = async (userId) => {
    if (!window.confirm("Revoke all active sessions for this user?")) {
      return;
    }

    setActionLoading(`revoke-all-${userId}`);
    setError("");

    try {
      const response = await apiFetch(`/users/${userId}/sessions`, {
        method: "DELETE",
      });

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || "Failed to revoke sessions");
      }

      setSessions((prev) => ({
        ...prev,
        [userId]: [],
      }));
    } catch (err) {
      setError(err.message || "Failed to revoke sessions");
    } finally {
      setActionLoading(null);
    }
  };

  const formatDate = (value) => {
    if (!value) return "-";

    return new Date(value).toLocaleString();
  };

  if (loading) {
    return <div>Loading users...</div>;
  }

  return (
    <div>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "25px",
          gap: "15px",
          flexWrap: "wrap",
        }}
      >
        <div style={{ textAlign: "left" }}>
          <h1
            style={{
              margin: "0 0 8px 0",
              color: "#e2e8f0",
              fontSize: "1.6rem",
              fontWeight: "700",
              textAlign: "left",
            }}
          >
            User Management
          </h1>
          <p
            style={{
              color: "#94a3b8",
              margin: 0,
              fontSize: "0.9rem",
            }}
          >
            Manage users and active sessions.
          </p>
        </div>

        <button
          type="button"
          onClick={loadUsers}
          style={{
            padding: "9px 14px",
            background: "#334155",
            color: "#ffffff",
            border: "1px solid #475569",
            borderRadius: "6px",
            cursor: "pointer",
          }}
        >
          Refresh
        </button>
      </div>

      {error && (
        <div
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

      <div
        style={{
          overflowX: "auto",
          background: "#1e293b",
          borderRadius: "8px",
          border: "1px solid #334155",
        }}
      >
        <table
          style={{
            width: "100%",
            borderCollapse: "collapse",
            minWidth: "800px",
          }}
        >
          <thead>
            <tr style={{ background: "#0f172a" }}>
              <th style={headerStyle}>ID</th>
              <th style={headerStyle}>Username</th>
              <th style={headerStyle}>Email</th>
              <th style={headerStyle}>Role</th>
              <th style={headerStyle}>Status</th>
              <th style={headerStyle}>Actions</th>
            </tr>
          </thead>

          <tbody>
            {users.map((user) => {
              const isCurrentUser = user.id === currentUser.id;
              const isExpanded = expandedUserId === user.id;
              const userSessions = sessions[user.id] || [];

              return (
                <React.Fragment key={user.id}>
                  <tr>
                    <td style={cellStyle}>{user.id}</td>
                    <td style={cellStyle}>{user.username}</td>
                    <td style={cellStyle}>{user.email}</td>
                    <td style={cellStyle}>{user.role}</td>
                    <td style={cellStyle}>
                      <span
                        style={{
                          color: user.is_active ? "#4ade80" : "#f87171",
                          fontWeight: "600",
                        }}
                      >
                        {user.is_active ? "Active" : "Disabled"}
                      </span>
                    </td>
                    <td style={cellStyle}>
                      <div
                        style={{
                          display: "flex",
                          gap: "8px",
                          flexWrap: "wrap",
                        }}
                      >
                        <button
                          type="button"
                          onClick={() => loadSessions(user.id)}
                          disabled={
                            actionLoading === `sessions-${user.id}`
                          }
                          style={secondaryButtonStyle}
                        >
                          {isExpanded ? "Hide Sessions" : "Sessions"}
                        </button>

                        {user.is_active && !isCurrentUser && (
                          <button
                            type="button"
                            onClick={() => handleDisable(user.id)}
                            disabled={
                              actionLoading === `disable-${user.id}`
                            }
                            style={dangerButtonStyle}
                          >
                            {actionLoading === `disable-${user.id}`
                              ? "Disabling..."
                              : "Disable"}
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>

                  {isExpanded && (
                    <tr>
                      <td
                        colSpan="6"
                        style={{
                          padding: "18px",
                          background: "#0f172a",
                          borderTop: "1px solid #334155",
                        }}
                      >
                        <div
                          style={{
                            display: "flex",
                            justifyContent: "space-between",
                            alignItems: "center",
                            marginBottom: "12px",
                            gap: "10px",
                            flexWrap: "wrap",
                          }}
                        >
                          <strong style={{ color: "#e2e8f0" }}>
                            Active Sessions
                          </strong>

                          {userSessions.length > 0 && (
                            <button
                              type="button"
                              onClick={() => handleRevokeAll(user.id)}
                              disabled={
                                actionLoading ===
                                `revoke-all-${user.id}`
                              }
                              style={dangerButtonStyle}
                            >
                              {actionLoading ===
                              `revoke-all-${user.id}`
                                ? "Revoking..."
                                : "Revoke All"}
                            </button>
                          )}
                        </div>

                        {userSessions.length === 0 ? (
                          <div style={{ color: "#94a3b8" }}>
                            No active sessions.
                          </div>
                        ) : (
                          <div style={{ overflowX: "auto" }}>
                            <table
                              style={{
                                width: "100%",
                                borderCollapse: "collapse",
                                minWidth: "700px",
                              }}
                            >
                              <thead>
                                <tr>
                                  <th style={headerStyle}>Session ID</th>
                                  <th style={headerStyle}>Created</th>
                                  <th style={headerStyle}>Expires</th>
                                  <th style={headerStyle}>
                                    Last Activity
                                  </th>
                                  <th style={headerStyle}>Action</th>
                                </tr>
                              </thead>
                              <tbody>
                                {userSessions.map((session) => (
                                  <tr key={session.id}>
                                    <td style={cellStyle}>
                                      {session.id}
                                    </td>
                                    <td style={cellStyle}>
                                      {formatDate(session.created_at)}
                                    </td>
                                    <td style={cellStyle}>
                                      {formatDate(session.expires_at)}
                                    </td>
                                    <td style={cellStyle}>
                                      {formatDate(session.last_activity)}
                                    </td>
                                    <td style={cellStyle}>
                                      <button
                                        type="button"
                                        onClick={() =>
                                          handleRevokeSession(
                                            user.id,
                                            session.id
                                          )
                                        }
                                        disabled={
                                          actionLoading ===
                                          `revoke-${session.id}`
                                        }
                                        style={dangerButtonStyle}
                                      >
                                        {actionLoading ===
                                        `revoke-${session.id}`
                                          ? "Revoking..."
                                          : "Revoke"}
                                      </button>
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        )}
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

const headerStyle = {
  padding: "12px 14px",
  textAlign: "left",
  color: "#94a3b8",
  fontSize: "0.85rem",
  fontWeight: "600",
  borderBottom: "1px solid #334155",
};

const cellStyle = {
  padding: "12px 14px",
  color: "#e2e8f0",
  borderBottom: "1px solid #334155",
  verticalAlign: "top",
};

const secondaryButtonStyle = {
  padding: "7px 10px",
  background: "#334155",
  color: "#ffffff",
  border: "1px solid #475569",
  borderRadius: "5px",
  cursor: "pointer",
};

const dangerButtonStyle = {
  padding: "7px 10px",
  background: "#991b1b",
  color: "#ffffff",
  border: "1px solid #b91c1c",
  borderRadius: "5px",
  cursor: "pointer",
};
