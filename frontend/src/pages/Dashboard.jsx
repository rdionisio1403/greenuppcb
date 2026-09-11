import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch("/dashboard/summary")
      .then((res) => {
        if (!res.ok) throw new Error("HTTP error: " + res.status);
        return res.json();
      })
      .then((summary) => {
        setData(summary);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Dashboard fetch error:", err);
        setError("Failed to load dashboard metrics from backend.");
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div style={{ textAlign: "center", padding: "80px 0", color: "#38bdf8", fontSize: "1.1rem" }}>
        Loading laboratory telemetry...
      </div>
    );
  }

  if (error || !data) {
    return (
      <div style={{ maxWidth: "1200px", margin: "40px auto", backgroundColor: "#450a0a", border: "1px solid #7f1d1d", color: "#fecaca", padding: "16px", borderRadius: "8px", textAlign: "center" }}>
        {error || "Unable to render dashboard telemetry."}
      </div>
    );
  }

  const kpis = [
    {
      title: "Total PCBs Handled",
      value: data.total_pcbs,
      sub: `${data.pcbs_this_month} logged this month`,
      icon: "📦",
      gradient: "linear-gradient(135deg, rgba(14, 165, 233, 0.15) 0%, rgba(15, 23, 42, 0.6) 100%)",
      border: "#0ea5e9",
      accent: "#38bdf8"
    },
    {
      title: "Diagnostic & Repairs",
      value: data.repairs_completed,
      sub: "Active rework actions",
      icon: "🔧",
      gradient: "linear-gradient(135deg, rgba(245, 158, 11, 0.15) 0%, rgba(15, 23, 42, 0.6) 100%)",
      border: "#f59e0b",
      accent: "#fbbf24"
    },
    {
      title: "Quality Pass Rate",
      value: `${data.pass_rate ?? 100}%`,
      sub: `${data.tests_passed ?? 0} Pass / ${data.tests_failed ?? 0} Fail`,
      icon: "🎯",
      gradient: "linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(15, 23, 42, 0.6) 100%)",
      border: "#10b981",
      accent: "#34d399"
    },
    {
      title: "Tests Executed",
      value: data.tests_completed,
      sub: "Electrical & functional tests",
      icon: "⚡",
      gradient: "linear-gradient(135deg, rgba(168, 85, 247, 0.15) 0%, rgba(15, 23, 42, 0.6) 100%)",
      border: "#a855f7",
      accent: "#c084fc"
    }
  ];

  const statusList = [
    { label: "Registered", count: data.received ?? 0, color: "#38bdf8", bg: "rgba(56, 189, 248, 0.12)", border: "rgba(56, 189, 248, 0.3)" },
    { label: "In Diagnosis", count: data.in_diagnosis ?? 0, color: "#38bdf8", bg: "rgba(56, 189, 248, 0.12)", border: "rgba(56, 189, 248, 0.3)" },
    { label: "Repaired", count: data.repaired ?? 0, color: "#34d399", bg: "rgba(52, 211, 153, 0.12)", border: "rgba(52, 211, 153, 0.3)" },
    { label: "Testing", count: data.testing ?? 0, color: "#fbbf24", bg: "rgba(251, 191, 36, 0.12)", border: "rgba(251, 191, 36, 0.3)" },
    { label: "Completed", count: data.completed ?? 0, color: "#4ade80", bg: "rgba(74, 222, 128, 0.12)", border: "rgba(74, 222, 128, 0.3)" },
    { label: "Archived", count: data.archived ?? 0, color: "#fb923c", bg: "rgba(234, 88, 12, 0.15)", border: "rgba(234, 88, 12, 0.4)", badge: "🔒 Locked" },
  ];

  return (
    <div style={{ maxWidth: "1400px", margin: "0 auto", padding: "28px 20px", color: "#e6edf3", fontFamily: "Segoe UI, -apple-system, sans-serif" }}>
      
      {/* Top Banner */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: "26px", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <h1 style={{ margin: 0, fontSize: "1.75rem", fontWeight: "700", color: "#f8fafc", letterSpacing: "-0.5px" }}>
              Laboratory Overview Dashboard
            </h1>
            <span style={{ backgroundColor: "rgba(34, 197, 94, 0.15)", color: "#4ade80", border: "1px solid rgba(34, 197, 94, 0.3)", padding: "2px 10px", borderRadius: "12px", fontSize: "0.75rem", fontWeight: "700" }}>
              ● LIVE
            </span>
          </div>
          <p style={{ margin: "6px 0 0 0", color: "#94a3b8", fontSize: "0.92rem" }}>
            GreenUp PCB Lifecycle Management & Quality Assurance Telemetry
          </p>
        </div>
      </div>

      {/* Primary KPI Cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))", gap: "18px", marginBottom: "26px" }}>
        {kpis.map((kpi, idx) => (
          <div
            key={idx}
            style={{
              background: kpi.gradient,
              border: `1px solid ${kpi.border}44`,
              borderTop: `3px solid ${kpi.border}`,
              borderRadius: "10px",
              padding: "20px",
              boxShadow: "0 8px 24px rgba(0,0,0,0.3)"
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontSize: "0.82rem", color: "#94a3b8", fontWeight: "700", textTransform: "uppercase", letterSpacing: "0.5px" }}>
                {kpi.title}
              </span>
              <span style={{ fontSize: "1.4rem" }}>{kpi.icon}</span>
            </div>
            <div style={{ fontSize: "2.3rem", fontWeight: "800", color: kpi.accent, margin: "10px 0 4px 0", letterSpacing: "-1px" }}>
              {kpi.value}
            </div>
            <div style={{ fontSize: "0.8rem", color: "#64748b" }}>
              {kpi.sub}
            </div>
          </div>
        ))}
      </div>

      {/* Middle Section: Quality Yield Progress & Status Distribution */}
      <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1.8fr", gap: "20px", marginBottom: "26px" }}>
        
        {/* Quality Test Yield Widget */}
        <div style={{ backgroundColor: "#161b22", border: "1px solid #30363d", borderRadius: "10px", padding: "22px", boxShadow: "0 4px 16px rgba(0,0,0,0.25)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px" }}>
            <h3 style={{ margin: 0, fontSize: "1.05rem", fontWeight: "700", color: "#f0f6fc", display: "flex", alignItems: "center", gap: "8px" }}>
              <span>🧪</span> Quality Assurance Yield
            </h3>
            <span style={{ fontSize: "0.8rem", color: "#34d399", fontWeight: "700" }}>
              {data.tests_completed} Tests Evaluated
            </span>
          </div>

          <p style={{ margin: "0 0 16px 0", fontSize: "0.85rem", color: "#8b949e" }}>
            First-pass test ratio across all diagnostic and post-repair functional cycles.
          </p>

          <div style={{ height: "14px", width: "100%", backgroundColor: "#21262d", borderRadius: "8px", overflow: "hidden", display: "flex", marginBottom: "14px" }}>
            <div style={{ width: `${data.pass_rate ?? 100}%`, backgroundColor: "#238636", transition: "width 0.6s ease" }} />
            <div style={{ width: `${100 - (data.pass_rate ?? 100)}%`, backgroundColor: "#da3633" }} />
          </div>

          <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.85rem", color: "#8b949e" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              <span style={{ width: "10px", height: "10px", borderRadius: "50%", backgroundColor: "#238636", display: "inline-block" }}></span>
              Passed: <strong style={{ color: "#3fb950" }}>{data.tests_passed ?? 0}</strong>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              <span style={{ width: "10px", height: "10px", borderRadius: "50%", backgroundColor: "#da3633", display: "inline-block" }}></span>
              Failed: <strong style={{ color: "#f85149" }}>{data.tests_failed ?? 0}</strong>
            </div>
          </div>
        </div>

        {/* Operational Status Breakdown */}
        <div style={{ backgroundColor: "#161b22", border: "1px solid #30363d", borderRadius: "10px", padding: "22px", boxShadow: "0 4px 16px rgba(0,0,0,0.25)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
            <h3 style={{ margin: 0, fontSize: "1.05rem", fontWeight: "700", color: "#f0f6fc", display: "flex", alignItems: "center", gap: "8px" }}>
              <span>📊</span> Lifecycle Distribution
            </h3>
            <span style={{ fontSize: "0.8rem", color: "#8b949e" }}>Live status partitions</span>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "12px" }}>
            {statusList.map((st, idx) => (
              <div
                key={idx}
                style={{
                  backgroundColor: "#0d1117",
                  border: `1px solid ${st.border}`,
                  borderRadius: "8px",
                  padding: "14px 10px",
                  textAlign: "center"
                }}
              >
                <div style={{
                  display: "inline-block",
                  padding: "2px 8px",
                  backgroundColor: st.bg,
                  color: st.color,
                  borderRadius: "10px",
                  fontSize: "0.74rem",
                  fontWeight: "700"
                }}>
                  {st.badge ? `${st.badge} ${st.label}` : st.label}
                </div>
                <div style={{ fontSize: "1.6rem", fontWeight: "800", color: "#f0f6fc", marginTop: "8px" }}>
                  {st.count}
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>

      {/* Live Work In Progress Queue */}
      <div style={{ backgroundColor: "#161b22", border: "1px solid #30363d", borderRadius: "10px", padding: "22px", boxShadow: "0 4px 16px rgba(0,0,0,0.25)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px", flexWrap: "wrap", gap: "10px" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <h3 style={{ margin: 0, fontSize: "1.1rem", fontWeight: "700", color: "#f0f6fc", display: "flex", alignItems: "center", gap: "8px" }}>
                <span>🔄</span> Live Work-in-Progress (Recent Intake Queue)
              </h3>
              <span style={{
                backgroundColor: "rgba(56, 189, 248, 0.15)",
                color: "#38bdf8",
                border: "1px solid rgba(56, 189, 248, 0.3)",
                padding: "2px 8px",
                borderRadius: "10px",
                fontSize: "0.72rem",
                fontWeight: "700"
              }}>
                Showing Latest {data.recent_pcbs?.length || 0} of {data.total_pcbs}
              </span>
            </div>
            <span style={{ fontSize: "0.82rem", color: "#8b949e", marginTop: "4px", display: "inline-block" }}>
              Most recent units logged in the laboratory
            </span>
          </div>
          <Link to="/" style={{ color: "#58a6ff", fontSize: "0.85rem", textDecoration: "none", fontWeight: "600" }}>
            View All Registry →
          </Link>
        </div>

        {(!data.recent_pcbs || data.recent_pcbs.length === 0) ? (
          <p style={{ color: "#6e7681", fontSize: "0.9rem", margin: 0 }}>No active PCBs found in queue.</p>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "0.88rem" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid #30363d", color: "#8b949e", fontSize: "0.78rem", textTransform: "uppercase" }}>
                  <th style={{ padding: "10px 12px" }}>Reference</th>
                  <th style={{ padding: "10px 12px" }}>Serial</th>
                  <th style={{ padding: "10px 12px" }}>Equipment</th>
                  <th style={{ padding: "10px 12px" }}>Status</th>
                  <th style={{ padding: "10px 12px" }}>Received</th>
                  <th style={{ padding: "10px 12px", textAlign: "right" }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {data.recent_pcbs.map((p) => (
                  <tr key={p.id} style={{ borderBottom: "1px solid #21262d" }}>
                    <td style={{ padding: "12px", fontWeight: "700", color: "#58a6ff" }}>
                      {p.internal_reference}
                    </td>
                    <td style={{ padding: "12px", color: "#cbd5e1" }}>
                      {p.serial_number || "—"}
                    </td>
                    <td style={{ padding: "12px", color: "#cbd5e1" }}>
                      {p.equipment || "—"}
                    </td>
                    <td style={{ padding: "12px" }}>
                      <span style={{
                        padding: "3px 8px",
                        borderRadius: "10px",
                        fontSize: "0.72rem",
                        fontWeight: "700",
                        backgroundColor: p.status === "ARCHIVED" ? "rgba(234, 88, 12, 0.2)" : "rgba(56, 189, 248, 0.15)",
                        color: p.status === "ARCHIVED" ? "#fb923c" : "#38bdf8",
                        border: p.status === "ARCHIVED" ? "1px solid rgba(234, 88, 12, 0.4)" : "1px solid rgba(56, 189, 248, 0.3)"
                      }}>
                        {p.status}
                      </span>
                    </td>
                    <td style={{ padding: "12px", color: "#8b949e", fontSize: "0.82rem" }}>
                      {p.date_received}
                    </td>
                    <td style={{ padding: "12px", textAlign: "right" }}>
                      <Link
                        to={`/pcbs/${p.id}`}
                        style={{
                          padding: "4px 10px",
                          backgroundColor: "#21262d",
                          color: "#58a6ff",
                          border: "1px solid #30363d",
                          borderRadius: "5px",
                          textDecoration: "none",
                          fontSize: "0.78rem",
                          fontWeight: "600"
                        }}
                      >
                        Inspect
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

    </div>
  );
}
