import React from "react";
import { Link, Outlet } from "react-router-dom";

export default function Layout() {
  return (
    <div style={{ fontFamily: "sans-serif", maxWidth: "1000px", margin: "0 auto", padding: "20px" }}>
      <header style={{ borderBottom: "2px solid #2e7d32", paddingBottom: "10px", marginBottom: "20px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h2 style={{ margin: 0, color: "#2e7d32" }}>🌱 GreenUp PCB LIS</h2>
        <nav>
          <Link to="/" style={{ marginRight: "15px", textDecoration: "none", fontWeight: "bold" }}>PCB Listesi</Link>
          <Link to="/new" style={{ padding: "6px 12px", background: "#2e7d32", color: "#fff", textDecoration: "none", borderRadius: "4px" }}>+ Yeni PCB Ekle</Link>
        </nav>
      </header>
      <main>
        <Outlet />
      </main>
    </div>
  );
}
