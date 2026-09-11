import React, { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { createPCB } from "../api/pcbs";

export default function PCBCreate() {
  const navigate = useNavigate();
  const location = useLocation();

  const reintakeData = location.state?.reintake || null;

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

  useEffect(() => {
    if (reintakeData) {
      const serial = reintakeData.serial_number || "";
      const randomSuffix = Math.floor(1000 + Math.random() * 9000);
      const generatedRef = serial ? `RE-${serial}-${randomSuffix}` : `RE-PCB-${randomSuffix}`;

      setFormData((prev) => ({
        ...prev,
        internal_reference: generatedRef,
        customer_name: reintakeData.customer_name || "",
        equipment: reintakeData.equipment || "",
        manufacturer: reintakeData.manufacturer || "",
        pcb_model: reintakeData.pcb_model || "",
        serial_number: serial,
        failure_description: "",
      }));
    }
  }, [reintakeData]);

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
    <div style={{ maxWidth: "560px", margin: "0 auto", padding: "20px 0" }}>
      <h3 style={{ fontSize: "1.3rem", marginBottom: "18px", textAlign: "center", color: "#e2e8f0" }}>
        {reintakeData ? "🔁 Re-Intake PCB Entry (New Service Cycle)" : "Register New PCB Entry"}
      </h3>

      {reintakeData && (
        <div style={{ background: "rgba(234, 88, 12, 0.15)", border: "1px solid #ea580c", color: "#fdba74", padding: "10px 14px", borderRadius: "6px", marginBottom: "15px", fontSize: "0.85rem" }}>
          Re-intake initiated for serial <strong>{reintakeData.serial_number}</strong>. Reference format generated to prevent collision.
        </div>
      )}

      {error && (
        <div style={{ background: "#7f1d1d", color: "#fecaca", padding: "10px 14px", borderRadius: "6px", marginBottom: "15px", fontSize: "0.9rem" }}>
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
        <div>
          <label style={{ fontSize: "0.8rem", color: "#8b949e", display: "block", marginBottom: "4px" }}>Internal Reference *</label>
          <input
            required
            style={{ ...inputStyle, width: "100%", boxSizing: "border-box" }}
            placeholder="Internal Reference (e.g. PCB-2026-001)"
            value={formData.internal_reference}
            onChange={(e) => setFormData({ ...formData, internal_reference: e.target.value })}
          />
        </div>

        <div>
          <label style={{ fontSize: "0.8rem", color: "#8b949e", display: "block", marginBottom: "4px" }}>Serial Number *</label>
          <input
            required
            style={{ ...inputStyle, width: "100%", boxSizing: "border-box" }}
            placeholder="Serial Number (e.g. SN-987654)"
            value={formData.serial_number}
            onChange={(e) => setFormData({ ...formData, serial_number: e.target.value })}
          />
        </div>

        <div>
          <label style={{ fontSize: "0.8rem", color: "#8b949e", display: "block", marginBottom: "4px" }}>Customer Name</label>
          <input
            style={{ ...inputStyle, width: "100%", boxSizing: "border-box" }}
            placeholder="Customer Name"
            value={formData.customer_name}
            onChange={(e) => setFormData({ ...formData, customer_name: e.target.value })}
          />
        </div>

        <div>
          <label style={{ fontSize: "0.8rem", color: "#8b949e", display: "block", marginBottom: "4px" }}>Equipment *</label>
          <input
            required
            style={{ ...inputStyle, width: "100%", boxSizing: "border-box" }}
            placeholder="Equipment"
            value={formData.equipment}
            onChange={(e) => setFormData({ ...formData, equipment: e.target.value })}
          />
        </div>

        <div>
          <label style={{ fontSize: "0.8rem", color: "#8b949e", display: "block", marginBottom: "4px" }}>Manufacturer</label>
          <input
            style={{ ...inputStyle, width: "100%", boxSizing: "border-box" }}
            placeholder="Manufacturer"
            value={formData.manufacturer}
            onChange={(e) => setFormData({ ...formData, manufacturer: e.target.value })}
          />
        </div>

        <div>
          <label style={{ fontSize: "0.8rem", color: "#8b949e", display: "block", marginBottom: "4px" }}>PCB Model</label>
          <input
            style={{ ...inputStyle, width: "100%", boxSizing: "border-box" }}
            placeholder="PCB Model"
            value={formData.pcb_model}
            onChange={(e) => setFormData({ ...formData, pcb_model: e.target.value })}
          />
        </div>

        <div>
          <label style={{ fontSize: "0.8rem", color: "#8b949e", display: "block", marginBottom: "4px" }}>Received Date *</label>
          <input
            type="date"
            required
            style={{ ...inputStyle, width: "100%", boxSizing: "border-box" }}
            value={formData.date_received}
            onChange={(e) => setFormData({ ...formData, date_received: e.target.value })}
          />
        </div>

        <div>
          <label style={{ fontSize: "0.8rem", color: "#8b949e", display: "block", marginBottom: "4px" }}>Failure Description</label>
          <textarea
            style={{ ...inputStyle, width: "100%", boxSizing: "border-box", minHeight: "80px", fontFamily: "inherit" }}
            placeholder="Reported Failure / Incoming Fault"
            value={formData.failure_description}
            onChange={(e) => setFormData({ ...formData, failure_description: e.target.value })}
          />
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          style={{
            padding: "10px",
            backgroundColor: isSubmitting ? "#166534" : "#22c55e",
            color: "#ffffff",
            border: "none",
            borderRadius: "6px",
            fontWeight: "700",
            cursor: isSubmitting ? "not-allowed" : "pointer",
            marginTop: "10px"
          }}
        >
          {isSubmitting ? "Registering..." : reintakeData ? "Confirm Re-Intake Entry" : "Register PCB"}
        </button>
      </form>
    </div>
  );
}
