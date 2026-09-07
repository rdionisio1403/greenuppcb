import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { getPCB, addDiagnosis, addRepair, addTest, uploadPCBImage } from "../api/pcbs";

export default function PCBDetail() {
  const { id } = useParams();

  const handleDownloadPDF = async () => {
    try {
      const response = await fetch(`/pcbs/${id}/reports/download`);
      if (!response.ok) throw new Error("Download failed");
      
      // Backend'in dosya yolundan veya veritabanındaki rapor adından orijinal ismi alalım
      let filename = "inspection_report.pdf";
      if (pcb.reports && pcb.reports.length > 0 && pcb.reports[0].filename_path) {
        const parts = pcb.reports[0].filename_path.split("/");
        filename = parts[parts.length - 1];
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert("Failed to download PDF report: " + err.message);
    }
  };
  const [pcb, setPcb] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Form states matching exact inputs in the screenshot
  const [diagForm, setDiagForm] = useState({ technician: "", fault_found: "", recommended_action: "" });
  const [repairForm, setRepairForm] = useState({ technician: "", actions_taken: "", components_replaced: "" });
  const [testForm, setTestForm] = useState({ tester: "", test_type: "", result: "PASSED", notes: "" });

  // Image upload states
  const [uploadCategory, setUploadCategory] = useState("before");
  const [imageTechnician, setImageTechnician] = useState("");
  const [selectedTestId, setSelectedTestId] = useState("");
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);

  const loadData = () => {
    getPCB(id)
      .then((data) => {
        setPcb(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setError("Failed to load PCB details: " + (err.message || ""));
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
      setDiagForm({ technician: "", fault_found: "", recommended_action: "" });
      loadData();
    } catch (err) {
      alert("Error adding diagnosis: " + err.message);
    }
  };

  const handleAddRepair = async (e) => {
    e.preventDefault();
    try {
      await addRepair(id, repairForm);
      setRepairForm({ technician: "", actions_taken: "", components_replaced: "" });
      loadData();
    } catch (err) {
      alert("Error adding repair: " + err.message);
    }
  };

  const handleAddTest = async (e) => {
    e.preventDefault();
    try {
      await addTest(id, testForm);
      setTestForm({ tester: "", test_type: "", result: "PASSED", notes: "" });
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
      await uploadPCBImage(id, uploadCategory, selectedFile, imageTechnician || "Technician", selectedTestId || null);
      setSelectedFile(null);
      setImageTechnician("");
      setSelectedTestId("");
      e.target.reset();
      loadData();
    } catch (err) {
      alert("Image upload failed: " + err.message);
    } finally {
      setUploading(false);
    }
  };

  if (loading) {
    return <div style={{ textAlign: "center", padding: "60px 0", color: "#8b949e", fontSize: "1rem" }}>Loading PCB lifecycle records...</div>;
  }

  if (error || !pcb) {
    return (
      <div style={{ maxWidth: "1200px", margin: "40px auto", background: "#450a0a", border: "1px solid #7f1d1d", color: "#fecaca", padding: "16px", borderRadius: "8px", textAlign: "center" }}>
        Failed to load PCB details: {error || "Record not found."}
      </div>
    );
  }

  const latestPdfUrl = (pcb.reports && pcb.reports.length > 0 && pcb.reports[0].filename_path) 
    ? pcb.reports[0].filename_path 
    : `/pcbs/${id}/reports/download`;

  const inputStyle = {
    width: "100%",
    padding: "9px 12px",
    backgroundColor: "#0d1117",
    color: "#e6edf3",
    border: "1px solid #30363d",
    borderRadius: "6px",
    fontSize: "0.85rem",
    boxSizing: "border-box"
  };

  const btnSuccess = {
    padding: "8px 16px",
    backgroundColor: "#238636",
    color: "#ffffff",
    border: "1px solid rgba(240, 246, 252, 0.1)",
    borderRadius: "6px",
    fontWeight: "700",
    fontSize: "0.85rem",
    cursor: "pointer",
    display: "inline-block"
  };

  return (
    <div style={{ maxWidth: "1200px", margin: "0 auto", padding: "20px 16px", color: "#e6edf3", fontFamily: "Segoe UI, -apple-system, sans-serif" }}>
      
      {/* Top Navigation Bar */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
        <Link 
          to="/" 
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "6px",
            color: "#58a6ff",
            textDecoration: "none",
            fontSize: "0.92rem",
            fontWeight: "600"
          }}
        >
          ← Back to Registry
        </Link>
        <a 
          onClick={handleDownloadPDF}
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
            cursor: "pointer",
            border: "none"
          }}
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "8px",
            backgroundColor: "#1f6feb",
            color: "#ffffff",
            padding: "8px 16px",
            borderRadius: "6px",
            textDecoration: "none",
            fontWeight: "600",
            fontSize: "0.88rem",
            boxShadow: "0 2px 4px rgba(0,0,0,0.2)"
          }}
        >
          <span>📄</span> Download Inspection PDF
        </a>
      </div>

      {/* Main Board Info Card */}
      <div style={{ backgroundColor: "#161b22", border: "1px solid #30363d", borderRadius: "8px", padding: "24px", marginBottom: "24px", boxShadow: "0 4px 12px rgba(0,0,0,0.25)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "18px" }}>
          <div>
            <h2 style={{ margin: "0 0 6px 0", fontSize: "1.7rem", fontWeight: "700", letterSpacing: "-0.5px", color: "#f0f6fc" }}>
              {pcb.internal_reference}
            </h2>
            <div style={{ color: "#8b949e", fontSize: "0.95rem" }}>
              Equipment: <strong style={{ color: "#e6edf3" }}>{pcb.equipment}</strong>
            </div>
          </div>
          <span style={{
            backgroundColor: "rgba(31, 111, 235, 0.2)",
            color: "#58a6ff",
            border: "1px solid rgba(56, 139, 253, 0.4)",
            padding: "4px 14px",
            borderRadius: "20px",
            fontSize: "0.84rem",
            fontWeight: "600"
          }}>
            Status: {pcb.status}
          </span>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(190px, 1fr))", gap: "12px", padding: "16px", backgroundColor: "#0d1117", borderRadius: "6px", border: "1px solid #21262d", fontSize: "0.88rem" }}>
          <div><span style={{ color: "#8b949e" }}>Customer:</span> <strong style={{ color: "#f0f6fc" }}>{pcb.customer_name || "EcoPower Solutions"}</strong></div>
          <div><span style={{ color: "#8b949e" }}>Manufacturer:</span> <strong style={{ color: "#f0f6fc" }}>{pcb.manufacturer || "SMA Solar Technology"}</strong></div>
          <div><span style={{ color: "#8b949e" }}>PCB Model:</span> <strong style={{ color: "#f0f6fc" }}>{pcb.pcb_model || "INV-CTRL-5KW-V2"}</strong></div>
          <div><span style={{ color: "#8b949e" }}>Serial Number:</span> <strong style={{ color: "#f0f6fc" }}>{pcb.serial_number || "SN-SOLAR-2026-9901"}</strong></div>
          <div><span style={{ color: "#8b949e" }}>Received Date:</span> <strong style={{ color: "#f0f6fc" }}>{pcb.date_received || "2026-09-07"}</strong></div>
        </div>

        <div style={{ marginTop: "18px", textAlign: "center", padding: "14px", backgroundColor: "rgba(22, 27, 34, 0.7)", borderRadius: "6px", border: "1px dashed #30363d" }}>
          <span style={{ fontSize: "0.78rem", textTransform: "uppercase", letterSpacing: "1px", color: "#8b949e", fontWeight: "700" }}>REPORTED FAILURE:</span>
          <p style={{ margin: "6px 0 0 0", fontSize: "0.92rem", color: "#e6edf3", lineHeight: "1.5" }}>
            {pcb.failure_description || "Input fuse blown and shorted Schottky diode causing power rail grounding."}
          </p>
        </div>
      </div>

      {/* Grid 2 Sütun: Diagnosis (Sol) & Repairs (Sağ) */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px", marginBottom: "24px" }}>
        
        {/* Diagnosis Card */}
        <div style={{ backgroundColor: "#161b22", border: "1px solid #30363d", borderRadius: "8px", padding: "20px" }}>
          <h4 style={{ margin: "0 0 16px 0", color: "#58a6ff", fontSize: "1.08rem", display: "flex", alignItems: "center", gap: "8px" }}>
            <span>🩺</span> Diagnosis ({pcb.diagnoses ? pcb.diagnoses.length : 0})
          </h4>

          <div style={{ display: "flex", flexDirection: "column", gap: "12px", marginBottom: "18px", maxHeight: "260px", overflowY: "auto", paddingRight: "6px", maxHeight: "260px", overflowY: "auto", paddingRight: "6px" }}>
            {(!pcb.diagnoses || pcb.diagnoses.length === 0) ? (
              <p style={{ color: "#6e7681", fontSize: "0.85rem", margin: 0 }}>No diagnosis logged yet.</p>
            ) : (
              pcb.diagnoses.map((d) => (
                <div key={d.id} style={{ backgroundColor: "#0d1117", border: "1px solid #21262d", borderRadius: "6px", padding: "14px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                    <strong style={{ color: "#58a6ff", fontSize: "0.92rem" }}>{d.technician}</strong>
                    <span style={{ color: "#8b949e", fontSize: "0.78rem" }}>{d.diagnosis_date ? String(d.diagnosis_date).split("T")[0] : "2026-09-07"}</span>
                  </div>
                  <p style={{ margin: "0 0 8px 0", fontSize: "0.88rem", color: "#e6edf3", textAlign: "center", lineHeight: "1.4" }}>
                    {d.fault_found || d.findings}
                  </p>
                  {(d.recommended_action || d.recommendation) && (
                    <div style={{ fontSize: "0.82rem", fontStyle: "italic", color: "#8b949e", textAlign: "center", borderTop: "1px solid #21262d", paddingTop: "6px" }}>
                      Rec: {d.recommended_action || d.recommendation}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>

          <form onSubmit={handleAddDiagnosis} style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
            <input 
              required 
              style={inputStyle} 
              placeholder="Technician Name" 
              value={diagForm.technician} 
              onChange={(e) => setDiagForm({ ...diagForm, technician: e.target.value })} 
            />
            <input 
              required 
              style={inputStyle} 
              placeholder="Diagnostic Findings (fault found)" 
              value={diagForm.fault_found} 
              onChange={(e) => setDiagForm({ ...diagForm, fault_found: e.target.value })} 
            />
            <input 
              style={inputStyle} 
              placeholder="Recommended Action (optional)" 
              value={diagForm.recommended_action} 
              onChange={(e) => setDiagForm({ ...diagForm, recommended_action: e.target.value })} 
            />
            <div>
              <button type="submit" style={btnSuccess}>+ Add Diagnosis</button>
            </div>
          </form>
        </div>

        {/* Repairs Card */}
        <div style={{ backgroundColor: "#161b22", border: "1px solid #30363d", borderRadius: "8px", padding: "20px" }}>
          <h4 style={{ margin: "0 0 16px 0", color: "#f0883e", fontSize: "1.08rem", display: "flex", alignItems: "center", gap: "8px" }}>
            <span>🔧</span> Repairs ({pcb.repairs ? pcb.repairs.length : 0})
          </h4>

          <div style={{ display: "flex", flexDirection: "column", gap: "12px", marginBottom: "18px", maxHeight: "260px", overflowY: "auto", paddingRight: "6px" }}>
            {(!pcb.repairs || pcb.repairs.length === 0) ? (
              <p style={{ color: "#6e7681", fontSize: "0.85rem", margin: 0 }}>No repair actions logged yet.</p>
            ) : (
              pcb.repairs.map((r) => (
                <div key={r.id} style={{ backgroundColor: "#0d1117", border: "1px solid #21262d", borderRadius: "6px", padding: "14px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                    <strong style={{ color: "#f0883e", fontSize: "0.92rem" }}>{r.technician}</strong>
                    <span style={{ color: "#8b949e", fontSize: "0.78rem" }}>{r.repair_date ? String(r.repair_date).split("T")[0] : "2026-09-07"}</span>
                  </div>
                  <p style={{ margin: "0 0 8px 0", fontSize: "0.88rem", color: "#e6edf3", textAlign: "center", lineHeight: "1.4" }}>
                    {r.actions_taken || r.action_taken}
                  </p>
                  {(r.components_replaced || r.replaced) && (
                    <div style={{ fontSize: "0.82rem", color: "#8b949e", textAlign: "center", borderTop: "1px solid #21262d", paddingTop: "6px" }}>
                      Replaced: <span style={{ color: "#d29922" }}>{r.components_replaced || r.replaced}</span>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>

          <form onSubmit={handleAddRepair} style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
            <input 
              required 
              style={inputStyle} 
              placeholder="Technician Name" 
              value={repairForm.technician} 
              onChange={(e) => setRepairForm({ ...repairForm, technician: e.target.value })} 
            />
            <input 
              required 
              style={inputStyle} 
              placeholder="Actions Taken" 
              value={repairForm.actions_taken} 
              onChange={(e) => setRepairForm({ ...repairForm, actions_taken: e.target.value })} 
            />
            <input 
              style={inputStyle} 
              placeholder="Components Replaced (optional)" 
              value={repairForm.components_replaced} 
              onChange={(e) => setRepairForm({ ...repairForm, components_replaced: e.target.value })} 
            />
            <div>
              <button type="submit" style={btnSuccess}>+ Add Repair</button>
            </div>
          </form>
        </div>

      </div>

      {/* Tests Card - 3. Görseldeki Geniş Format */}
      <div style={{ backgroundColor: "#161b22", border: "1px solid #30363d", borderRadius: "8px", padding: "20px", marginBottom: "24px" }}>
        <h4 style={{ margin: "0 0 16px 0", color: "#3fb950", fontSize: "1.08rem", display: "flex", alignItems: "center", gap: "8px" }}>
          <span>✅</span> Tests ({pcb.tests ? pcb.tests.length : 0})
        </h4>

        <div style={{ display: "flex", flexDirection: "column", gap: "12px", marginBottom: "18px" , maxHeight: "260px", overflowY: "auto", paddingRight: "6px"}}>
          {(!pcb.tests || pcb.tests.length === 0) ? (
            <p style={{ color: "#6e7681", fontSize: "0.85rem", margin: 0 }}>No tests executed yet.</p>
          ) : (
            pcb.tests.map((t) => {
              const isPassed = (t.result || "").toUpperCase() === "PASSED";
              return (
                <div key={t.id} style={{ backgroundColor: "#0d1117", border: "1px solid #21262d", borderRadius: "6px", padding: "16px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                    <strong style={{ color: "#3fb950", fontSize: "0.95rem" }}>{t.tester || t.technician}</strong>
                    <span style={{
                      backgroundColor: isPassed ? "rgba(35, 134, 54, 0.2)" : "rgba(218, 54, 51, 0.2)",
                      color: isPassed ? "#3fb950" : "#f85149",
                      border: isPassed ? "1px solid rgba(46, 160, 67, 0.4)" : "1px solid rgba(248, 81, 73, 0.4)",
                      padding: "2px 8px",
                      borderRadius: "4px",
                      fontSize: "0.75rem",
                      fontWeight: "700"
                    }}>
                      {t.result}
                    </span>
                  </div>
                  <div style={{ textAlign: "center", fontWeight: "700", color: "#f0f6fc", fontSize: "0.98rem", margin: "6px 0" }}>
                    {t.test_type}
                  </div>
                  {t.notes && (
                    <p style={{ margin: "6px 0 0 0", textAlign: "center", fontSize: "0.86rem", color: "#8b949e", lineHeight: "1.4" }}>
                      {t.notes}
                    </p>
                  )}
                </div>
              );
            })
          )}
        </div>

        <form onSubmit={handleAddTest} style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
          <input 
            required 
            style={inputStyle} 
            placeholder="Tester / Technician Name" 
            value={testForm.tester} 
            onChange={(e) => setTestForm({ ...testForm, tester: e.target.value })} 
          />
          <input 
            required 
            style={inputStyle} 
            placeholder="Test Type (e.g. DC Load)" 
            value={testForm.test_type} 
            onChange={(e) => setTestForm({ ...testForm, test_type: e.target.value })} 
          />
          <select 
            style={inputStyle} 
            value={testForm.result} 
            onChange={(e) => setTestForm({ ...testForm, result: e.target.value })}
          >
            <option value="PASSED">PASSED</option>
            <option value="FAILED">FAILED</option>
          </select>
          <input 
            style={inputStyle} 
            placeholder="Test Notes (optional)" 
            value={testForm.notes} 
            onChange={(e) => setTestForm({ ...testForm, notes: e.target.value })} 
          />
          <div>
            <button type="submit" style={btnSuccess}>+ Add Test</button>
          </div>
        </form>
      </div>

      {/* Visual Inspection Images Section */}
      <div style={{ backgroundColor: "#161b22", border: "1px solid #30363d", borderRadius: "8px", padding: "20px" }}>
        <h4 style={{ margin: "0 0 16px 0", color: "#e6edf3", fontSize: "1.08rem", display: "flex", alignItems: "center", gap: "8px" }}>
          <span>📷</span> Inspection & Defect Images ({pcb.images ? pcb.images.length : 0})
        </h4>

        {/* Upload Bar */}
        <form onSubmit={handleImageUpload} style={{ display: "flex", flexWrap: "wrap", gap: "12px", alignItems: "center", padding: "14px", backgroundColor: "#0d1117", borderRadius: "6px", border: "1px solid #21262d", marginBottom: "20px" }}>
          <select
            value={uploadCategory}
            onChange={(e) => setUploadCategory(e.target.value)}
            style={{ padding: "8px 12px", backgroundColor: "#161b22", color: "#e6edf3", border: "1px solid #30363d", borderRadius: "6px", fontSize: "0.85rem" }}
          >
            <option value="before">Before Repair</option>
            <option value="during">During Test</option>
            <option value="defect">Defect</option>
            <option value="after">After Repair</option>
          </select>

          {/* Yazarak arama yapılabilen (datalist destekli) teknisyen inputu */}
          <input
            type="text"
            list="technicians-list"
            placeholder="Technician Name (e.g. Sema)"
            value={imageTechnician}
            onChange={(e) => {
              setImageTechnician(e.target.value);
              setSelectedTestId("");
            }}
            style={{ padding: "8px 12px", backgroundColor: "#161b22", color: "#e6edf3", border: "1px solid #30363d", borderRadius: "6px", fontSize: "0.85rem", width: "190px" }}
          />
          <datalist id="technicians-list">
            {Array.from(new Set([
              ...(pcb.diagnoses || []).map(d => d.technician),
              ...(pcb.repairs || []).map(r => r.technician),
              ...(pcb.tests || []).map(t => t.tester || t.technician)
            ])).filter(Boolean).map((tech, idx) => (
              <option key={idx} value={tech} />
            ))}
          </datalist>

          {/* Teknisyene göre büyük/küçük harf duyarsız filtrelenen testler */}
          <select
            value={selectedTestId}
            onChange={(e) => setSelectedTestId(e.target.value)}
            style={{ padding: "8px 12px", backgroundColor: "#161b22", color: "#e6edf3", border: "1px solid #30363d", borderRadius: "6px", fontSize: "0.85rem" }}
          >
            <option value="">Linked Test: None (General)</option>
            {(pcb.tests || [])
              .filter(t => {
                if (!imageTechnician.trim()) return true;
                const tName = (t.tester || t.technician || "").trim().toLowerCase();
                const sName = imageTechnician.trim().toLowerCase();
                return tName.includes(sName);
              })
              .map((t) => (
                <option key={t.id} value={t.id}>Linked Test: {t.test_type} ({t.tester || t.technician})</option>
              ))}
          </select>

          <input
            type="file"
            accept="image/*"
            onChange={(e) => setSelectedFile(e.target.files[0])}
            style={{ fontSize: "0.85rem", color: "#8b949e" }}
          />

          <button
            type="submit"
            disabled={uploading}
            style={{ 
              padding: "8px 16px",
              backgroundColor: "#238636",
              color: "#ffffff",
              border: "1px solid rgba(240, 246, 252, 0.1)",
              borderRadius: "6px",
              fontWeight: "700",
              fontSize: "0.85rem",
              cursor: "pointer",
              opacity: uploading ? 0.7 : 1 
            }}
          >
            {uploading ? "Uploading..." : "+ Upload Image"}
          </button>
        </form>

        {/* Images Grid */}
        {(!pcb.images || pcb.images.length === 0) ? (
          <p style={{ color: "#6e7681", fontSize: "0.88rem", margin: 0 }}>No inspection images uploaded for this PCB yet.</p>
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))", gap: "16px" }}>
            {pcb.images.map((img) => {
              const matchedTest = (pcb.tests || []).find((t) => t.id === img.test_id);
              return (
                <div key={img.id} style={{ border: "1px solid #30363d", borderRadius: "6px", overflow: "hidden", backgroundColor: "#0d1117" }}>
                  <a href={img.filename_path} target="_blank" rel="noreferrer">
                    <img
                      src={img.filename_path}
                      alt={img.category}
                      style={{ width: "100%", height: "140px", objectFit: "cover", display: "block" }}
                    />
                  </a>
                  <div style={{ padding: "10px" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                      <span style={{ fontSize: "0.75rem", textTransform: "uppercase", padding: "2px 8px", borderRadius: "4px", backgroundColor: "#21262d", color: "#58a6ff", fontWeight: "700" }}>
                        {img.category}
                      </span>
                      <span style={{ fontSize: "0.72rem", color: "#8b949e" }}>#{img.id}</span>
                    </div>
                    {matchedTest && (
                      <div style={{ fontSize: "0.72rem", color: "#38bdf8", backgroundColor: "rgba(56, 189, 248, 0.1)", padding: "2px 6px", borderRadius: "4px", border: "1px solid rgba(56, 189, 248, 0.2)" }}>
                        🧪 {matchedTest.test_type}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

    </div>
  );
}
