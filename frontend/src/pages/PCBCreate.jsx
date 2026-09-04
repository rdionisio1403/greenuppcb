import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { createPCB } from "../api/pcbs";

export default function PCBCreate() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    internal_reference: "",
    customer_name: "",
    equipment: "",
    manufacturer: "",
    pcb_model: "",
    serial_number: "",
    date_received: new Date().toISOString().split("T")[0],
    failure_description: "",
  });
  const [error, setError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);
    try {
      await createPCB(formData);
      navigate("/");
    } catch (err) {
      setError(err.message || "Failed to register PCB");
    } finally {
      setIsSubmitting(false);
    }
  };

  const inputStyle = {
    padding: "10px 12px",
    borderRadius: "6px",
    border: "1px solid #3f444e",
    backgroundColor: "#1e222b",
    color: "#f0f2f5",
    fontSize: "0.95rem"
  };

  return (
    <div style={{ maxWidth: "560px", margin: "0 auto" }}>
      <h3 style={{ fontSize: "1.3rem", marginBottom: "18px", textAlign: "center", color: "#e2e8f0" }}>
        Register New PCB Entry
      </h3>
      {error && (
        <div style={{ background: "#7f1d1d", color: "#fecaca", padding: "10px 14px", borderRadius: "6px", marginBottom: "15px", fontSize: "0.9rem" }}>
          {error}
        </div>
      )}
      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
        <input
          required
          style={inputStyle}
          placeholder="Internal Reference (e.g. PCB-2026-001)"
          value={formData.internal_reference}
          onChange={(e) => setFormData({ ...formData, internal_reference: e.target.value })}
        />
        <input
          required
          style={inputStyle}
          placeholder="Customer / Client Name"
          value={formData.customer_name}
          onChange={(e) => setFormData({ ...formData, customer_name: e.target.value })}
        />
        <input
          required
          style={inputStyle}
          placeholder="Equipment / Machine Name"
          value={formData.equipment}
          onChange={(e) => setFormData({ ...formData, equipment: e.target.value })}
        />
        <input
          style={inputStyle}
          placeholder="Manufacturer (Brand)"
          value={formData.manufacturer}
          onChange={(e) => setFormData({ ...formData, manufacturer: e.target.value })}
        />
        <input
          style={inputStyle}
          placeholder="PCB Model / Part Number"
          value={formData.pcb_model}
          onChange={(e) => setFormData({ ...formData, pcb_model: e.target.value })}
        />
        <input
          style={inputStyle}
          placeholder="Serial Number"
          value={formData.serial_number}
          onChange={(e) => setFormData({ ...formData, serial_number: e.target.value })}
        />
        <input
          type="date"
          required
          style={inputStyle}
          value={formData.date_received}
          onChange={(e) => setFormData({ ...formData, date_received: e.target.value })}
        />
        <textarea
          required
          rows="4"
          style={{ ...inputStyle, resize: "vertical", fontFamily: "inherit" }}
          placeholder="Fault / Failure Description..."
          value={formData.failure_description}
          onChange={(e) => setFormData({ ...formData, failure_description: e.target.value })}
        />
        <button
          type="submit"
          disabled={isSubmitting}
          style={{
            padding: "12px",
            background: isSubmitting ? "#1e5322" : "#2e7d32",
            color: "#fff",
            border: "none",
            borderRadius: "6px",
            cursor: isSubmitting ? "not-allowed" : "pointer",
            fontWeight: "600",
            fontSize: "1rem",
            marginTop: "6px",
            boxShadow: "0 2px 5px rgba(0,0,0,0.2)"
          }}
        >
          {isSubmitting ? "Saving..." : "Save Record"}
        </button>
      </form>
    </div>
  );
}
