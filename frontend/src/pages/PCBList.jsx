import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getPCBs } from "../api/pcbs";

export default function PCBList() {
  const [pcbs, setPcbs] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchPCBs = (q = "") => {
    setLoading(true);
    getPCBs(q)
      .then((data) => {
        setPcbs(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchPCBs();
  }, []);

  // Kullanıcı arama kutusuna yazdığında tetiklenen fonksiyon
  const handleSearchChange = (e) => {
    const val = e.target.value;
    setSearchQuery(val);
    fetchPCBs(val);
  };

  const getStatusBadge = (status) => {
    const raw = (status || "received").toLowerCase();
    const map = {
      received: { label: "Received", bg: "#1e3a8a", text: "#93c5fd" },
      under_diagnosis: { label: "Under Diagnosis", bg: "#854d0e", text: "#fef08a" },
      diagnosed: { label: "Diagnosed", bg: "#3730a3", text: "#c7d2fe" },
      under_repair: { label: "Under Repair", bg: "#9a3412", text: "#fed7aa" },
      repaired: { label: "Repaired", bg: "#065f46", text: "#a7f3d0" },
      tested_passed: { label: "Tested (Passed)", bg: "#14532d", text: "#86efac" },
      scrapped: { label: "Scrapped", bg: "#7f1d1d", text: "#fca5a5" },
    };

    const style = map[raw] || {
      label: raw.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
      bg: "#334155",
      text: "#cbd5e1",
    };

    return (
      <span
        style={{
          display: "inline-block",
          padding: "4px 10px",
          borderRadius: "9999px",
          fontSize: "0.78rem",
          fontWeight: "600",
          letterSpacing: "0.03em",
          backgroundColor: style.bg,
          color: style.text,
          whiteSpace: "nowrap",
        }}
      >
        {style.label}
      </span>
    );
  };

  return (
    <div>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "18px",
          flexWrap: "wrap",
          gap: "12px",
        }}
      >
        <div>
          <h3 style={{ margin: "0 0 4px 0", fontSize: "1.35rem", color: "#f1f5f9" }}>
            Registered PCB Units
          </h3>
          <p style={{ margin: 0, fontSize: "0.88rem", color: "#94a3b8" }}>
            Total {pcbs.length} board{pcbs.length === 1 ? "" : "s"} found
          </p>
        </div>

        {/* Server-Side Arama Çubuğu */}
        <div style={{ position: "relative", minWidth: "300px" }}>
          <input
            type="text"
            placeholder="Search reference, customer, model..."
            value={searchQuery}
            onChange={handleSearchChange}
            style={{
              width: "100%",
              padding: "9px 14px",
              borderRadius: "6px",
              border: "1px solid #30363d",
              backgroundColor: "#161b22",
              color: "#f0f6fc",
              fontSize: "0.9rem",
              boxSizing: "border-box",
              outline: "none",
            }}
          />
        </div>
      </div>

      {error && (
        <div style={{ background: "#7f1d1d", color: "#fecaca", padding: "14px", borderRadius: "8px", marginBottom: "16px" }}>
          Failed to load PCB registry: {error}
        </div>
      )}

      <div
        style={{
          backgroundColor: "#161b22",
          borderRadius: "8px",
          border: "1px solid #30363d",
          overflowX: "auto",
          boxShadow: "0 4px 12px rgba(0,0,0,0.25)",
        }}
      >
        <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left" }}>
          <thead>
            <tr style={{ backgroundColor: "#21262d", borderBottom: "1px solid #30363d" }}>
              <th style={{ padding: "12px 16px", color: "#8b949e", fontSize: "0.82rem", textTransform: "uppercase" }}>ID</th>
              <th style={{ padding: "12px 16px", color: "#8b949e", fontSize: "0.82rem", textTransform: "uppercase" }}>Reference</th>
              <th style={{ padding: "12px 16px", color: "#8b949e", fontSize: "0.82rem", textTransform: "uppercase" }}>Customer</th>
              <th style={{ padding: "12px 16px", color: "#8b949e", fontSize: "0.82rem", textTransform: "uppercase" }}>Equipment</th>
              <th style={{ padding: "12px 16px", color: "#8b949e", fontSize: "0.82rem", textTransform: "uppercase" }}>Status</th>
              <th style={{ padding: "12px 16px", color: "#8b949e", fontSize: "0.82rem", textTransform: "uppercase" }}>Received Date</th>
              <th style={{ padding: "12px 16px", color: "#8b949e", fontSize: "0.82rem", textTransform: "uppercase", textAlign: "center" }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan="7" style={{ padding: "30px", textAlign: "center", color: "#8b949e" }}>
                  Searching PCB records...
                </td>
              </tr>
            ) : pcbs.length === 0 ? (
              <tr>
                <td colSpan="7" style={{ padding: "30px", textAlign: "center", color: "#8b949e" }}>
                  {searchQuery ? `No records matching "${searchQuery}"` : "No PCB records found."}
                </td>
              </tr>
            ) : (
              pcbs.map((pcb) => (
                <tr
                  key={pcb.id}
                  style={{
                    borderBottom: "1px solid #21262d",
                    transition: "background-color 0.15s ease",
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "#1c2128")}
                  onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "transparent")}
                >
                  <td style={{ padding: "12px 16px", color: "#64748b", fontSize: "0.9rem" }}>#{pcb.id}</td>
                  <td style={{ padding: "12px 16px", fontWeight: "600", color: "#f1f5f9", fontSize: "0.92rem" }}>
                    {pcb.internal_reference}
                  </td>
                  <td style={{ padding: "12px 16px", color: "#cbd5e1", fontSize: "0.9rem" }}>
                    {pcb.customer_name || <span style={{ color: "#64748b" }}>—</span>}
                  </td>
                  <td style={{ padding: "12px 16px", color: "#cbd5e1", fontSize: "0.9rem" }}>
                    {pcb.equipment || <span style={{ color: "#64748b" }}>—</span>}
                  </td>
                  <td style={{ padding: "12px 16px" }}>{getStatusBadge(pcb.status)}</td>
                  <td style={{ padding: "12px 16px", color: "#94a3b8", fontSize: "0.88rem" }}>
                    {pcb.date_received || "—"}
                  </td>
                  <td style={{ padding: "12px 16px", textAlign: "center" }}>
                    <Link
                      to={`/pcbs/${pcb.id}`}
                      style={{
                        padding: "6px 12px",
                        backgroundColor: "#238636",
                        color: "#ffffff",
                        textDecoration: "none",
                        borderRadius: "5px",
                        fontSize: "0.82rem",
                        fontWeight: "600",
                        display: "inline-block",
                      }}
                    >
                      View Details
                    </Link>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
