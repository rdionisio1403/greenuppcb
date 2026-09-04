import React from "react";
import { Link, Outlet } from "react-router-dom";

export default function Layout() {
  return (
    <div style={{ fontFamily: "Segoe UI, Tahoma, Geneva, Verdana, sans-serif", maxWidth: "1100px", margin: "0 auto", padding: "20px" }}>
      <header
        style={{
          borderBottom: "2px solid #2e7d32",
          paddingBottom: "15px",
          marginBottom: "30px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "15px"
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <span style={{ fontSize: "1.5rem" }}>🌱</span>
          <h2 style={{ margin: 0, color: "#2e7d32", fontSize: "1.4rem", fontWeight: "700", whiteSpace: "nowrap" }}>
            GreenUp PCB LIS
          </h2>
        </div>
        <nav style={{ display: "flex", alignItems: "center", gap: "15px" }}>
          <Link
            to="/"
            style={{
              color: "#a0aec0",
              textDecoration: "none",
              fontWeight: "600",
              fontSize: "0.95rem",
              padding: "6px 10px",
              borderRadius: "4px"
            }}
          >
            PCB Registry
          </Link>
          <Link
            to="/new"
            style={{
              padding: "8px 16px",
              background: "#2e7d32",
              color: "#ffffff",
              textDecoration: "none",
              borderRadius: "6px",
              fontWeight: "600",
              fontSize: "0.95rem",
              boxShadow: "0 2px 4px rgba(0,0,0,0.15)"
            }}
          >
            + Register New PCB
          </Link>
        </nav>
      </header>
      <main>
        <Outlet />
      </main>
    </div>
  );
}
