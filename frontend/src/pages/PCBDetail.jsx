import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { getPCB, addDiagnosis, addRepair, addTest, getPCBImages, uploadPCBImage } from "../api/pcbs";

export default function PCBDetail() {
  const { id } = useParams();
  const [pcb, setPcb] = useState(null);
  const [images, setImages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Form states
  const [diagForm, setDiagForm] = useState({ technician: "", findings: "" });
  const [repairForm, setRepairForm] = useState({ technician: "", action_taken: "" });
  const [testForm, setTestForm] = useState({ technician: "", test_type: "", result: "PASSED" });

  // Image upload state
  const [uploadCategory, setUploadCategory] = useState("before");
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);

  const loadData = () => {
    Promise.all([getPCB(id), getPCBImages(id)])
      .then(([pcbData, imgData]) => {
        setPcb(pcbData);
        setImages(imgData || []);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  };

  useEffect(() => {
    loadData();
  }, [id]);

  const handleAddDiagnosis = async (e) => {
    e.preventDefault();
    try {
      await addDiagnosis(id, diagForm);
      setDiagForm({ technician: "", findings: "" });
      loadData();
    } catch (err) {
      alert("Error adding diagnosis: " + err.message);
    }
  };

  const handleAddRepair = async (e) => {
    e.preventDefault();
    try {
      await addRepair(id, repairForm);
      setRepairForm({ technician: "", action_taken: "" });
      loadData();
    } catch (err) {
      alert("Error adding repair: " + err.message);
    }
  };

  const handleAddTest = async (e) => {
    e.preventDefault();
    try {
      await addTest(id, testForm);
      setTestForm({ technician: "", test_type: "", result: "PASSED" });
      loadData();
    } catch (err) {
      alert("Error adding test: " + err.message);
    }
  };

  const handleImageUpload = async (e) => {
    e.preventDefault();
    if (!selectedFile) {
      alert("Please select an image file first.");
      return;
    }
    setUploading(true);
    try {
      await uploadPCBImage(id, uploadCategory, selectedFile);
      setSelectedFile(null);
      e.target.reset();
      loadData();
    } catch (err) {
      alert("Image upload failed: " + err.message);
    } finally {
      setUploading(false);
    }
  };

  if (loading) {
    return <div style={{ textAlign: "center", padding: "50px 0", color: "#94a3b8" }}>Loading PCB lifecycle records...</div>;
  }

  if (error || !pcb) {
    return (
      <div style={{ background: "#7f1d1d", color: "#fecaca", padding: "14px", borderRadius: "8px" }}>
        Failed to load PCB details: {error || "Record not found."}
      </div>
    );
  }

  const inputStyle = {
    width: "100%",
    padding: "8px 10px",
    borderRadius: "5px",
    border: "1px solid #30363d",
    backgroundColor: "#0d1117",
    color: "#f0f6fc",
    fontSize: "0.85rem",
    boxSizing: "border-box",
  };

  const btnStyle = {
    padding: "8px 14px",
    background: "#238636",
    color: "#ffffff",
    border: "none",
    borderRadius: "5px",
    fontWeight: "600",
    fontSize: "0.85rem",
    cursor: "pointer",
    alignSelf: "flex-start",
  };

  return (
    <div style={{ color: "#e6edf3" }}>
      {/* Top Breadcrumb & PDF Button */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px", flexWrap: "wrap", gap: "10px" }}>
        <Link to="/" style={{ color: "#58a6ff", textDecoration: "none", fontSize: "0.9rem", fontWeight: "500" }}>
          &larr; Back to Registry
        </Link>
        <a
          href={`/pcbs/${pcb.id}/reports/download`}
          target="_blank"
          rel="noopener noreferrer"
          style={{
            padding: "8px 16px",
            backgroundColor: "#1f6feb",
            color: "#ffffff",
            textDecoration: "none",
            borderRadius: "6px",
            fontSize: "0.88rem",
            fontWeight: "600",
            display: "inline-flex",
            alignItems: "center",
            gap: "8px",
            boxShadow: "0 2px 4px rgba(0,0,0,0.2)",
          }}
        >
          <span>📄</span> Download Inspection PDF
        </a>
      </div>

      {/* Main Board Info Card */}
      <div
        style={{
          backgroundColor: "#161b22",
          border: "1px solid #30363d",
          borderRadius: "8px",
          padding: "24px",
          marginBottom: "24px",
          boxShadow: "0 4px 12px rgba(0,0,0,0.25)",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "12px", borderBottom: "1px solid #21262d", paddingBottom: "16px", marginBottom: "16px" }}>
          <div>
            <h2 style={{ margin: "0 0 6px 0", color: "#f0f6fc", fontSize: "1.5rem" }}>
              {pcb.internal_reference}
            </h2>
            <span style={{ color: "#8b949e", fontSize: "0.95rem" }}>
              Equipment: <strong style={{ color: "#c9d1d9" }}>{pcb.equipment || "—"}</strong>
            </span>
          </div>
          <div style={{ textAlign: "right" }}>
            <span style={{ display: "inline-block", padding: "5px 12px", borderRadius: "9999px", background: "#1e3a8a", color: "#93c5fd", fontWeight: "600", fontSize: "0.82rem" }}>
              Status: {pcb.status}
            </span>
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "16px", fontSize: "0.9rem", color: "#8b949e" }}>
          <div>Customer: <span style={{ color: "#c9d1d9", fontWeight: "500" }}>{pcb.customer_name || "—"}</span></div>
          <div>Manufacturer: <span style={{ color: "#c9d1d9", fontWeight: "500" }}>{pcb.manufacturer || "—"}</span></div>
          <div>PCB Model: <span style={{ color: "#c9d1d9", fontWeight: "500" }}>{pcb.pcb_model || "—"}</span></div>
          <div>Serial Number: <span style={{ color: "#c9d1d9", fontWeight: "500" }}>{pcb.serial_number || "—"}</span></div>
          <div>Received Date: <span style={{ color: "#c9d1d9", fontWeight: "500" }}>{pcb.date_received || "—"}</span></div>
        </div>

        {pcb.failure_description && (
          <div style={{ marginTop: "18px", paddingTop: "14px", borderTop: "1px solid #21262d" }}>
            <span style={{ color: "#8b949e", fontSize: "0.85rem", fontWeight: "600", textTransform: "uppercase" }}>Reported Failure:</span>
            <p style={{ margin: "6px 0 0 0", color: "#e6edf3", fontSize: "0.92rem", lineHeight: "1.5" }}>
              {pcb.failure_description}
            </p>
          </div>
        )}
      </div>

      {/* Lifecycle Stage Columns */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: "20px", marginBottom: "24px" }}>
        
        {/* Diagnosis Card */}
        <div style={{ backgroundColor: "#161b22", border: "1px solid #30363d", borderRadius: "8px", padding: "18px" }}>
          <h4 style={{ margin: "0 0 14px 0", color: "#93c5fd", fontSize: "1.05rem", display: "flex", alignItems: "center", gap: "8px" }}>
            <span>🩺</span> Diagnosis ({pcb.diagnoses ? pcb.diagnoses.length : 0})
          </h4>
          <div style={{ maxHeight: "180px", overflowY: "auto", marginBottom: "14px" }}>
            {(!pcb.diagnoses || pcb.diagnoses.length === 0) ? (
              <p style={{ color: "#6e7681", fontSize: "0.85rem" }}>No diagnosis logged yet.</p>
            ) : (
              pcb.diagnoses.map((d, idx) => (
                <div key={idx} style={{ background: "#0d1117", border: "1px solid #21262d", borderRadius: "6px", padding: "10px", marginBottom: "8px", fontSize: "0.85rem" }}>
                  <div style={{ fontWeight: "600", color: "#58a6ff" }}>{d.technician}</div>
                  <div style={{ color: "#c9d1d9", marginTop: "4px" }}>{d.findings}</div>
                </div>
              ))
            )}
          </div>
          <form onSubmit={handleAddDiagnosis} style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            <input required style={inputStyle} placeholder="Technician Name" value={diagForm.technician} onChange={(e) => setDiagForm({ ...diagForm, technician: e.target.value })} />
            <input required style={inputStyle} placeholder="Diagnostic Findings" value={diagForm.findings} onChange={(e) => setDiagForm({ ...diagForm, findings: e.target.value })} />
            <button type="submit" style={btnStyle}>+ Add Diagnosis</button>
          </form>
        </div>

        {/* Repair Card */}
        <div style={{ backgroundColor: "#161b22", border: "1px solid #30363d", borderRadius: "8px", padding: "18px" }}>
          <h4 style={{ margin: "0 0 14px 0", color: "#fed7aa", fontSize: "1.05rem", display: "flex", alignItems: "center", gap: "8px" }}>
            <span>🔧</span> Repairs ({pcb.repairs ? pcb.repairs.length : 0})
          </h4>
          <div style={{ maxHeight: "180px", overflowY: "auto", marginBottom: "14px" }}>
            {(!pcb.repairs || pcb.repairs.length === 0) ? (
              <p style={{ color: "#6e7681", fontSize: "0.85rem" }}>No repair actions logged yet.</p>
            ) : (
              pcb.repairs.map((r, idx) => (
                <div key={idx} style={{ background: "#0d1117", border: "1px solid #21262d", borderRadius: "6px", padding: "10px", marginBottom: "8px", fontSize: "0.85rem" }}>
                  <div style={{ fontWeight: "600", color: "#f0883e" }}>{r.technician}</div>
                  <div style={{ color: "#c9d1d9", marginTop: "4px" }}>{r.action_taken}</div>
                </div>
              ))
            )}
          </div>
          <form onSubmit={handleAddRepair} style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            <input required style={inputStyle} placeholder="Technician Name" value={repairForm.technician} onChange={(e) => setRepairForm({ ...repairForm, technician: e.target.value })} />
            <input required style={inputStyle} placeholder="Action Taken / Components" value={repairForm.action_taken} onChange={(e) => setRepairForm({ ...repairForm, action_taken: e.target.value })} />
            <button type="submit" style={btnStyle}>+ Add Repair</button>
          </form>
        </div>

        {/* Test Card */}
        <div style={{ backgroundColor: "#161b22", border: "1px solid #30363d", borderRadius: "8px", padding: "18px" }}>
          <h4 style={{ margin: "0 0 14px 0", color: "#a7f3d0", fontSize: "1.05rem", display: "flex", alignItems: "center", gap: "8px" }}>
            <span>✅</span> Tests ({pcb.tests ? pcb.tests.length : 0})
          </h4>
          <div style={{ maxHeight: "180px", overflowY: "auto", marginBottom: "14px" }}>
            {(!pcb.tests || pcb.tests.length === 0) ? (
              <p style={{ color: "#6e7681", fontSize: "0.85rem" }}>No test runs logged yet.</p>
            ) : (
              pcb.tests.map((t, idx) => (
                <div key={idx} style={{ background: "#0d1117", border: "1px solid #21262d", borderRadius: "6px", padding: "10px", marginBottom: "8px", fontSize: "0.85rem" }}>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ fontWeight: "600", color: "#3fb950" }}>{t.technician}</span>
                    <span style={{ fontSize: "0.75rem", padding: "2px 6px", borderRadius: "4px", backgroundColor: t.result === "PASSED" ? "#14532d" : "#7f1d1d", color: "#fff" }}>
                      {t.result}
                    </span>
                  </div>
                  <div style={{ color: "#c9d1d9", marginTop: "4px" }}>{t.test_type}</div>
                </div>
              ))
            )}
          </div>
          <form onSubmit={handleAddTest} style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            <input required style={inputStyle} placeholder="Technician Name" value={testForm.technician} onChange={(e) => setTestForm({ ...testForm, technician: e.target.value })} />
            <input required style={inputStyle} placeholder="Test Type (e.g. DC Load)" value={testForm.test_type} onChange={(e) => setTestForm({ ...testForm, test_type: e.target.value })} />
            <select style={inputStyle} value={testForm.result} onChange={(e) => setTestForm({ ...testForm, result: e.target.value })}>
              <option value="PASSED">PASSED</option>
              <option value="FAILED">FAILED</option>
            </select>
            <button type="submit" style={btnStyle}>+ Add Test</button>
          </form>
        </div>
      </div>

      {/* Visual Inspection Images Section */}
      <div style={{ backgroundColor: "#161b22", border: "1px solid #30363d", borderRadius: "8px", padding: "20px" }}>
        <h4 style={{ margin: "0 0 16px 0", color: "#e6edf3", fontSize: "1.1rem", display: "flex", alignItems: "center", gap: "8px" }}>
          <span>📷</span> Inspection & Defect Images ({images.length})
        </h4>

        {/* Upload Bar */}
        <form onSubmit={handleImageUpload} style={{ display: "flex", flexWrap: "wrap", gap: "12px", alignItems: "center", padding: "14px", backgroundColor: "#0d1117", borderRadius: "6px", border: "1px solid #21262d", marginBottom: "20px" }}>
          <select
            style={{ ...inputStyle, width: "auto", minWidth: "140px" }}
            value={uploadCategory}
            onChange={(e) => setUploadCategory(e.target.value)}
          >
            <option value="before">Before Repair</option>
            <option value="during">During Inspection</option>
            <option value="after">After Repair</option>
            <option value="defect">Defect Close-up</option>
          </select>
          <input
            type="file"
            accept="image/*"
            required
            onChange={(e) => setSelectedFile(e.target.files[0])}
            style={{ fontSize: "0.85rem", color: "#8b949e" }}
          />
          <button type="submit" disabled={uploading} style={btnStyle}>
            {uploading ? "Uploading..." : "+ Upload Image"}
          </button>
        </form>

        {/* Gallery Grid */}
        {images.length === 0 ? (
          <p style={{ color: "#6e7681", fontSize: "0.88rem", margin: 0 }}>No inspection images uploaded for this PCB yet.</p>
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: "16px" }}>
            {images.map((img) => (
              <div key={img.id} style={{ border: "1px solid #30363d", borderRadius: "6px", overflow: "hidden", backgroundColor: "#0d1117" }}>
                <a href={img.filename_path} target="_blank" rel="noreferrer">
                  <img
                    src={img.filename_path}
                    alt={img.category}
                    style={{ width: "100%", height: "140px", objectFit: "cover", display: "block" }}
                  />
                </a>
                <div style={{ padding: "8px 10px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span style={{ fontSize: "0.75rem", textTransform: "uppercase", padding: "2px 6px", borderRadius: "4px", backgroundColor: "#21262d", color: "#58a6ff", fontWeight: "600" }}>
                    {img.category}
                  </span>
                  <span style={{ fontSize: "0.72rem", color: "#6e7681" }}>#{img.id}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
