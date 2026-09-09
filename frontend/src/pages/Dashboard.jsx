import React, { useEffect, useState } from "react";

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch("/dashboard/summary")
      .then((res) => {
        if (!res.ok) {
          throw new Error("HTTP error: " + res.status);
        }
        return res.json();
      })
      .then((data) => {
        setData(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Dashboard fetch error:", err);
        setError("Failed to load dashboard metrics from backend.");
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <div style={{ textAlign: "center", padding: "40px", color: "#666" }}>Loading dashboard summary...</div>;
  }

  if (error) {
    return <div style={{ padding: "15px", backgroundColor: "#ffebee", color: "#c62828", borderRadius: "6px" }}>{error}</div>;
  }

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "24px" }}>
        <div>
          <h2 style={{ margin: 0, color: "#f8fafc", fontSize: "1.5rem" }}>Laboratory Overview Dashboard</h2>
          <p style={{ margin: "4px 0 0 0", color: "#cbd5e1", fontSize: "0.9rem" }}>GreenUp PCB Lab • Week 10 Summary</p>
        </div>
      </div>

      {/* 4 Key Indicators */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "16px", marginBottom: "28px" }}>
        <div style={{ padding: "20px", background: "#f8fafc", borderRadius: "8px", borderLeft: "5px solid #3182ce", boxShadow: "0 1px 3px rgba(0,0,0,0.05)" }}>
          <div style={{ fontSize: "0.85rem", color: "#4a5568", fontWeight: "600", textTransform: "uppercase" }}>Total PCBs</div>
          <div style={{ fontSize: "2rem", fontWeight: "700", color: "#2b6cb0", marginTop: "8px" }}>{data.total_pcbs}</div>
        </div>

        <div style={{ padding: "20px", background: "#f8fafc", borderRadius: "8px", borderLeft: "5px solid #38a169", boxShadow: "0 1px 3px rgba(0,0,0,0.05)" }}>
          <div style={{ fontSize: "0.85rem", color: "#4a5568", fontWeight: "600", textTransform: "uppercase" }}>PCBs Received This Month</div>
          <div style={{ fontSize: "2rem", fontWeight: "700", color: "#2f855a", marginTop: "8px" }}>{data.pcbs_this_month}</div>
        </div>

        <div style={{ padding: "20px", background: "#f8fafc", borderRadius: "8px", borderLeft: "5px solid #00b4d8", boxShadow: "0 1px 3px rgba(0,0,0,0.05)" }}>
          <div style={{ fontSize: "0.85rem", color: "#4a5568", fontWeight: "600", textTransform: "uppercase" }}>Repairs Completed</div>
          <div style={{ fontSize: "2rem", fontWeight: "700", color: "#0077b6", marginTop: "8px" }}>{data.repairs_completed}</div>
        </div>

        <div style={{ padding: "20px", background: "#f8fafc", borderRadius: "8px", borderLeft: "5px solid #d69e2e", boxShadow: "0 1px 3px rgba(0,0,0,0.05)" }}>
          <div style={{ fontSize: "0.85rem", color: "#4a5568", fontWeight: "600", textTransform: "uppercase" }}>Tests Completed</div>
          <div style={{ fontSize: "2rem", fontWeight: "700", color: "#b7791f", marginTop: "8px" }}>{data.tests_completed}</div>
        </div>
      </div>

      {/* PCBs by Status */}
      <div style={{ background: "#ffffff", borderRadius: "8px", padding: "24px", border: "1px solid #e2e8f0", boxShadow: "0 1px 3px rgba(0,0,0,0.05)" }}>
        <h3 style={{ margin: "0 0 16px 0", fontSize: "1.1rem", color: "#f8fafc" }}>PCBs by Status</h3>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "16px", textAlign: "center" }}>
          <div style={{ padding: "16px", background: "#f7fafc", borderRadius: "6px" }}>
            <span style={{ display: "inline-block", padding: "4px 8px", background: "#e2e8f0", color: "#4a5568", borderRadius: "4px", fontSize: "0.8rem", fontWeight: "600" }}>Received</span>
            <div style={{ fontSize: "1.6rem", fontWeight: "700", color: "#4a5568", marginTop: "8px" }}>{data.received}</div>
          </div>
          <div style={{ padding: "16px", background: "#ebf8ff", borderRadius: "6px" }}>
            <span style={{ display: "inline-block", padding: "4px 8px", background: "#bee3f8", color: "#2b6cb0", borderRadius: "4px", fontSize: "0.8rem", fontWeight: "600" }}>In Diagnosis</span>
            <div style={{ fontSize: "1.6rem", fontWeight: "700", color: "#2b6cb0", marginTop: "8px" }}>{data.in_diagnosis}</div>
          </div>
          <div style={{ padding: "16px", background: "#f0fff4", borderRadius: "6px" }}>
            <span style={{ display: "inline-block", padding: "4px 8px", background: "#c6f6d5", color: "#2f855a", borderRadius: "4px", fontSize: "0.8rem", fontWeight: "600" }}>Repaired</span>
            <div style={{ fontSize: "1.6rem", fontWeight: "700", color: "#2f855a", marginTop: "8px" }}>{data.repaired}</div>
          </div>
          <div style={{ padding: "16px", background: "#edf2f7", borderRadius: "6px" }}>
            <span style={{ display: "inline-block", padding: "4px 8px", background: "#cbd5e0", color: "#1a202c", borderRadius: "4px", fontSize: "0.8rem", fontWeight: "600" }}>Closed</span>
            <div style={{ fontSize: "1.6rem", fontWeight: "700", color: "#1a202c", marginTop: "8px" }}>{data.closed}</div>
          </div>
        </div>
      </div>
    </div>
  );
}
