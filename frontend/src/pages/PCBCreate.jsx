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

const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await createPCB(formData);
      navigate("/");
    } catch (err) {
      setError(err.message);
    }
  };

return (
    <div style={{ maxWidth: "500px" }}>
      <h3>Yeni PCB Kaydı</h3>
      {error && <p style={{ color: "red" }}>{error}</p>}
      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
        <input required placeholder="Referans No (örn: REF-2026-001)" value={formData.internal_reference} onChange={(e) => setFormData({ ...formData, internal_reference: e.target.value })} />
        <input required placeholder="Müşteri Adı" value={formData.customer_name} onChange={(e) => setFormData({ ...formData, customer_name: e.target.value })} />
        <input required placeholder="Ekipman" value={formData.equipment} onChange={(e) => setFormData({ ...formData, equipment: e.target.value })} />
        <input placeholder="Üretici" value={formData.manufacturer} onChange={(e) => setFormData({ ...formData, manufacturer: e.target.value })} />
        <input placeholder="PCB Modeli" value={formData.pcb_model} onChange={(e) => setFormData({ ...formData, pcb_model: e.target.value })} />
        <input placeholder="Seri Numarası" value={formData.serial_number} onChange={(e) => setFormData({ ...formData, serial_number: e.target.value })} />
        <input type="date" required value={formData.date_received} onChange={(e) => setFormData({ ...formData, date_received: e.target.value })} />
        <textarea required placeholder="Arıza Açıklaması" value={formData.failure_description} onChange={(e) => setFormData({ ...formData, failure_description: e.target.value })} />
        <button type="submit" style={{ padding: "10px", background: "#2e7d32", color: "#fff", border: "none", borderRadius: "4px", cursor: "pointer" }}>Kaydet</button>
      </form>
    </div>
  );
}
