import React, { useEffect, useState } from "react";
import { useParams, Link, useNavigate, useOutletContext } from "react-router-dom";
import { getPCB, updatePCB, addDiagnosis, addRepair, addTest, uploadPCBImage, updateDiagnosis, updateRepair, updateTest, replacePCBImage, deletePCBImage, deleteDiagnosis, deleteRepair } from "../api/pcbs";
import { apiFetch } from "../api/apiFetch";
import { Pencil, Trash2 } from "lucide-react";

export default function PCBDetail() {

  const { user } = useOutletContext();
  const { id } = useParams();
  const navigate = useNavigate();

  const [pcb, setPcb] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [statusDraft, setStatusDraft] = useState("REGISTERED");
  const [savingStatus, setSavingStatus] = useState(false);

  // Duplicate submission protection flags
  const [savingDiag, setSavingDiag] = useState(false);
  const [generatingReport, setGeneratingReport] = useState(false);
  const [savingRepair, setSavingRepair] = useState(false);
  const [savingTest, setSavingTest] = useState(false);

  // Form states
  const [diagForm, setDiagForm] = useState({ technician: "", fault_found: "", recommended_action: "" });
  const [repairForm, setRepairForm] = useState({ technician: "", actions_taken: "", components_replaced: "" });

  const [editingDiagnosisId, setEditingDiagnosisId] = useState(null);
  const [diagnosisEditForm, setDiagnosisEditForm] = useState({});
  const [savingDiagnosisEdit, setSavingDiagnosisEdit] = useState(false);
  const [deletingDiagnosisId, setDeletingDiagnosisId] = useState(null);
  const [editingRepairId, setEditingRepairId] = useState(null);
  const [repairEditForm, setRepairEditForm] = useState({});
  const [savingRepairEdit, setSavingRepairEdit] = useState(false);
  const [deletingRepairId, setDeletingRepairId] = useState(null);
  const [testForm, setTestForm] = useState({ tester: "", test_type: "", result: "", notes: "" });
  const [editingTestId, setEditingTestId] = useState(null);
  const [testEditForm, setTestEditForm] = useState({});
  const [savingTestEdit, setSavingTestEdit] = useState(false);

  // Image upload states
  const [uploadCategory, setUploadCategory] = useState("before");
  const [imageTechnician, setImageTechnician] = useState("");
  const [selectedTestId, setSelectedTestId] = useState("");
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [editingImageId, setEditingImageId] = useState(null);
  const [imageEditForm, setImageEditForm] = useState({
    category: "before",
    technician: "",
    test_id: "",
  });
  const [imageEditFile, setImageEditFile] = useState(null);
  const [savingImageEdit, setSavingImageEdit] = useState(false);
  const [deletingImageId, setDeletingImageId] = useState(null);

  const loadData = () => {
    getPCB(id)
      .then((data) => {
        setPcb(data);
        setStatusDraft(data.status || "REGISTERED");
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setError(err.message || "Record not found.");
        setLoading(false);
      });
  };

  useEffect(() => {
    loadData();
  }, [id]);

  const handleStatusUpdate = async () => {
    if (!pcb || pcb.is_archived || savingStatus) return;
    if (statusDraft === pcb.status) return;

    setSavingStatus(true);
    try {
      const updated = await updatePCB(id, { status: statusDraft });
      setPcb((current) => ({ ...current, ...updated }));
      setStatusDraft(updated.status || statusDraft);
      alert("PCB status updated successfully.");
    } catch (err) {
      alert("Failed to update PCB status: " + err.message);
    } finally {
      setSavingStatus(false);
    }
  };

  const handleGenerateReport = async () => {
    if (generatingReport) return;
    setGeneratingReport(true);
    try {
      const response = await apiFetch(`/pcbs/${id}/reports/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" }
      });
      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || "Report generation failed");
      }
      alert("Inspection report compiled successfully!");
      await loadData();
    } catch (err) {
      alert("Failed to generate report: " + err.message);
    } finally {
      setGeneratingReport(false);
    }
  };

  const handleDownloadPDF = async () => {
    try {
      const response = await apiFetch(`/pcbs/${id}/reports/download`);
      if (!response.ok) throw new Error("Download failed");
      
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
      alert("Failed to download report: " + err.message);
    }
  };

  const handleAddDiagnosis = async (e) => {
    e.preventDefault();
    if (savingDiag) return;
    setSavingDiag(true);
    try {
      await addDiagnosis(id, diagForm);
      setDiagForm({ technician: "", fault_found: "", recommended_action: "" });
      loadData();
    } catch (err) {
      alert("Failed to add diagnosis: " + err.message);
    } finally {
      setSavingDiag(false);
    }
  };

  const handleAddRepair = async (e) => {
    e.preventDefault();
    if (savingRepair) return;
    setSavingRepair(true);
    try {
      await addRepair(id, repairForm);
      setRepairForm({ technician: "", actions_taken: "", components_replaced: "" });
      loadData();
    } catch (err) {
      alert("Failed to add repair: " + err.message);
    } finally {
      setSavingRepair(false);
    }
  };


  const handleSaveDiagnosisEdit = async (e) => {
    e.preventDefault();
    if (savingDiagnosisEdit || editingDiagnosisId === null) return;
    setSavingDiagnosisEdit(true);
    try {
      await updateDiagnosis(id, editingDiagnosisId, diagnosisEditForm);
      setEditingDiagnosisId(null);
      setDiagnosisEditForm({});
      await loadData();
      alert("Diagnosis updated successfully.");
    } catch (err) {
      alert("Failed to update diagnosis: " + err.message);
    } finally {
      setSavingDiagnosisEdit(false);
    }
  };

  const handleSaveRepairEdit = async (e) => {
    e.preventDefault();
    if (savingRepairEdit || editingRepairId === null) return;
    setSavingRepairEdit(true);
    try {
      await updateRepair(id, editingRepairId, repairEditForm);
      setEditingRepairId(null);
      setRepairEditForm({});
      await loadData();
      alert("Repair updated successfully.");
    } catch (err) {
      alert("Failed to update repair: " + err.message);
    } finally {
      setSavingRepairEdit(false);
    }
  };

  const handleDeleteDiagnosis = async (diagnosisId) => {
    if (user?.role !== "admin" || deletingDiagnosisId !== null) return;
    const confirmed = window.confirm(
      "Delete this diagnosis permanently? This action cannot be undone."
    );
    if (!confirmed) return;

    setDeletingDiagnosisId(diagnosisId);
    try {
      await deleteDiagnosis(id, diagnosisId);
      if (editingDiagnosisId === diagnosisId) {
        setEditingDiagnosisId(null);
        setDiagnosisEditForm({});
      }
      await loadData();
      alert("Diagnosis deleted successfully.");
    } catch (err) {
      alert("Failed to delete diagnosis: " + err.message);
    } finally {
      setDeletingDiagnosisId(null);
    }
  };

  const handleDeleteRepair = async (repairId) => {
    if (user?.role !== "admin" || deletingRepairId !== null) return;
    const confirmed = window.confirm(
      "Delete this repair record permanently? This action cannot be undone."
    );
    if (!confirmed) return;

    setDeletingRepairId(repairId);
    try {
      await deleteRepair(id, repairId);
      if (editingRepairId === repairId) {
        setEditingRepairId(null);
        setRepairEditForm({});
      }
      await loadData();
      alert("Repair record deleted successfully.");
    } catch (err) {
      alert("Failed to delete repair: " + err.message);
    } finally {
      setDeletingRepairId(null);
    }
  };

  const handleAddTest = async (e) => {
    e.preventDefault();
    if (savingTest) return;
    setSavingTest(true);
    try {
      await addTest(id, testForm);
      setTestForm({ tester: "", test_type: "", result: "", notes: "" });
      loadData();
    } catch (err) {
      alert("Failed to add test: " + err.message);
    } finally {
      setSavingTest(false);
    }
  };

  const handleSaveTestEdit = async (e) => {
    e.preventDefault();
    if (savingTestEdit || editingTestId === null) return;

    setSavingTestEdit(true);
    try {
      await updateTest(id, editingTestId, testEditForm);
      setEditingTestId(null);
      setTestEditForm({});
      loadData();
      alert("Test updated successfully.");
    } catch (err) {
      alert("Failed to update test: " + err.message);
    } finally {
      setSavingTestEdit(false);
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
      const formData = new FormData();
      formData.append("category", uploadCategory);
      formData.append("technician", imageTechnician || "Technician");

      if (selectedTestId) {
        formData.append("test_id", selectedTestId);
      }

      formData.append("file", selectedFile);

      await uploadPCBImage(id, formData);

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

  const startImageEdit = (img) => {
    setEditingImageId(img.id);
    setImageEditForm({
      category: img.category || "before",
      technician: img.technician || "",
      test_id: img.test_id == null ? "" : String(img.test_id),
    });
    setImageEditFile(null);
  };

  const cancelImageEdit = () => {
    setEditingImageId(null);
    setImageEditForm({ category: "before", technician: "", test_id: "" });
    setImageEditFile(null);
  };

  const handleSaveImageEdit = async (e, imageId) => {
    e.preventDefault();
    if (savingImageEdit || !imageEditFile) {
      if (!imageEditFile) alert("Please select a replacement image file.");
      return;
    }

    setSavingImageEdit(true);
    try {
      const formData = new FormData();
      formData.append("category", imageEditForm.category);
      formData.append("technician", imageEditForm.technician || "Technician");
      if (imageEditForm.test_id) formData.append("test_id", imageEditForm.test_id);
      formData.append("file", imageEditFile);

      await replacePCBImage(id, imageId, formData);
      cancelImageEdit();
      loadData();
      alert("Image updated successfully.");
    } catch (err) {
      alert("Failed to update image: " + err.message);
    } finally {
      setSavingImageEdit(false);
    }
  };

  const handleDeleteImage = async (imageId) => {
    if (deletingImageId !== null) return;
    if (!window.confirm("Delete this inspection image permanently?")) return;

    setDeletingImageId(imageId);
    try {
      await deletePCBImage(id, imageId);
      if (editingImageId === imageId) cancelImageEdit();
      loadData();
      alert("Image deleted successfully.");
    } catch (err) {
      alert("Failed to delete image: " + err.message);
    } finally {
      setDeletingImageId(null);
    }
  };

  if (loading) {
    return <div style={{ textAlign: "center", padding: "60px 0", color: "#8b949e", fontSize: "1rem" }}>Loading PCB lifecycle records...</div>;
  }

  if (error || !pcb) {
    return (
      <div style={{ maxWidth: "1200px", margin: "40px auto", background: "#450a0a", border: "1px solid #7f1d1d", color: "#fecaca", padding: "16px", borderRadius: "8px", textAlign: "center" }}>
        {error || "Record not found."}
      </div>
    );
  }

  const isTestLocked = (test) => {
    if (test.is_locked !== undefined) return test.is_locked;
    if (!test.test_date) return false;
    const testDate = new Date(test.test_date);
    const now = new Date();
    const diffDays = (now - testDate) / (1000 * 60 * 60 * 24);
    return diffDays > 365;
  };

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

  const smallEditButton = {
    padding: "5px 9px",
    backgroundColor: "#21262d",
    color: "#e6edf3",
    border: "1px solid #30363d",
    borderRadius: "5px",
    cursor: "pointer",
    fontSize: "0.78rem",
  };

  const btnSuccess = (disabled) => ({
    padding: "8px 16px",
    backgroundColor: disabled ? "#21262d" : "#238636",
    color: disabled ? "#8b949e" : "#ffffff",
    border: "1px solid rgba(240, 246, 252, 0.1)",
    borderRadius: "6px",
    fontWeight: "700",
    fontSize: "0.85rem",
    cursor: disabled ? "not-allowed" : "pointer",
    display: "inline-block"
  });

  const lockedNotice = (
    <div style={{ padding: "12px", backgroundColor: "rgba(234, 88, 12, 0.1)", border: "1px dashed rgba(234, 88, 12, 0.4)", borderRadius: "6px", color: "#fdba74", fontSize: "0.82rem", textAlign: "center" }}>
      🔒 Record is archived and immutable under quality audit rules.
    </div>
  );

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
        <div style={{ display: "flex", gap: "10px" }}>

          <button
            onClick={handleGenerateReport}
            disabled={generatingReport}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "8px",
              backgroundColor: generatingReport ? "#238636aa" : "#238636",
              color: "#ffffff",
              padding: "8px 16px",
              borderRadius: "6px",
              fontWeight: "600",
              fontSize: "0.88rem",
              cursor: generatingReport ? "not-allowed" : "pointer",
              border: "none",
              boxShadow: "0 2px 4px rgba(0,0,0,0.2)"
            }}
          >
            <span>{generatingReport ? "⏳" : "⚡"}</span> {generatingReport ? "Generating..." : "Generate Report"}
          </button>

          <button
            onClick={handleDownloadPDF}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "8px",
              backgroundColor: "#1f6feb",
              color: "#ffffff",
              padding: "8px 16px",
              borderRadius: "6px",
              fontSize: "0.88rem",
              fontWeight: "600",
              cursor: "pointer",
              border: "none",
              boxShadow: "0 2px 4px rgba(0,0,0,0.2)"
            }}
          >
            <span>📄</span> Download Inspection PDF
          </button>
        </div>
      </div>

      {/* Archived Notice Banner & Re-Intake Option */}
      {pcb.is_archived && (
        <div style={{
          backgroundColor: "rgba(124, 45, 18, 0.25)",
          border: "1px solid #ea580c",
          borderRadius: "8px",
          padding: "14px 18px",
          marginBottom: "20px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "12px"
        }}>
          <div>
            <div style={{ fontWeight: "700", color: "#fdba74", fontSize: "0.95rem", display: "flex", alignItems: "center", gap: "6px" }}>
              <span>🔒</span> Quality Audit Rule: Unit Archived & Immutable
            </div>
            <div style={{ color: "#fed7aa", fontSize: "0.84rem", marginTop: "4px" }}>
              All tests on this board are older than 1 year or unit lifecycle has closed. Direct edits are disabled.
            </div>
          </div>
          <button
            onClick={() => navigate("/new", {
              state: {
                reintake: {
                  serial_number: pcb.serial_number || "",
                  customer_id: pcb.customer_id || "",
                  equipment: pcb.equipment || "",
                  manufacturer: pcb.manufacturer || "",
                  pcb_model: pcb.pcb_model || "",
                }
              }
            })}
            style={{
              backgroundColor: "#ea580c",
              color: "#ffffff",
              border: "none",
              padding: "8px 16px",
              borderRadius: "6px",
              fontWeight: "700",
              fontSize: "0.85rem",
              cursor: "pointer",
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
              boxShadow: "0 2px 6px rgba(234, 88, 12, 0.3)"
            }}
          >
            <span>🔁</span> Re-Intake PCB (Start New Service Cycle)
          </button>
        </div>
      )}

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
          <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
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
            {!pcb.is_archived && (
              <div style={{ display: "flex", gap: "6px", alignItems: "center", flexWrap: "wrap" }}>
                <select
                  aria-label="PCB status"
                  value={statusDraft}
                  disabled={savingStatus}
                  onChange={(e) => setStatusDraft(e.target.value)}
                  style={{
                    backgroundColor: "#0d1117",
                    color: "#e6edf3",
                    border: "1px solid #30363d",
                    borderRadius: "6px",
                    padding: "6px 8px",
                    fontSize: "0.82rem",
                    maxWidth: "170px"
                  }}
                >
                  <option value="REGISTERED">Registered</option>
                  <option value="IN_DIAGNOSIS">In Diagnosis</option>
                  <option value="REPAIRED">Repaired</option>
                  <option value="TESTING">Testing</option>
                  <option value="COMPLETED">Completed</option>
                </select>
                <button
                  type="button"
                  disabled={savingStatus || statusDraft === pcb.status}
                  onClick={handleStatusUpdate}
                  style={{
                    padding: "7px 10px",
                    backgroundColor: savingStatus || statusDraft === pcb.status ? "#21262d" : "#238636",
                    color: savingStatus || statusDraft === pcb.status ? "#8b949e" : "#ffffff",
                    border: "1px solid #30363d",
                    borderRadius: "6px",
                    cursor: savingStatus || statusDraft === pcb.status ? "not-allowed" : "pointer",
                    fontSize: "0.82rem",
                    fontWeight: "600"
                  }}
                >
                  {savingStatus ? "Saving..." : "Save Status"}
                </button>
              </div>
            )}
            {pcb.is_archived && (
              <span style={{
                backgroundColor: "rgba(234, 88, 12, 0.2)",
                color: "#fb923c",
                border: "1px solid rgba(234, 88, 12, 0.5)",
                padding: "4px 12px",
                borderRadius: "20px",
                fontSize: "0.82rem",
                fontWeight: "700"
              }}>
                🔒 ARCHIVED
              </span>
            )}
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(190px, 1fr))", gap: "12px", padding: "16px", backgroundColor: "#0d1117", borderRadius: "6px", border: "1px solid #21262d", fontSize: "0.88rem" }}>
          <div><span style={{ color: "#8b949e" }}>Customer:</span> <strong style={{ color: "#f0f6fc" }}>{pcb.customer_name || "-"}</strong></div>
          <div><span style={{ color: "#8b949e" }}>Manufacturer:</span> <strong style={{ color: "#f0f6fc" }}>{pcb.manufacturer || "-"}</strong></div>
          <div><span style={{ color: "#8b949e" }}>PCB Model:</span> <strong style={{ color: "#f0f6fc" }}>{pcb.pcb_model || "-"}</strong></div>
          <div><span style={{ color: "#8b949e" }}>Serial Number:</span> <strong style={{ color: "#f0f6fc" }}>{pcb.serial_number || "-"}</strong></div>
          <div><span style={{ color: "#8b949e" }}>Received Date:</span> <strong style={{ color: "#f0f6fc" }}>{pcb.date_received || "-"}</strong></div>
        </div>

        <div style={{ marginTop: "18px", textAlign: "center", padding: "14px", backgroundColor: "rgba(22, 27, 34, 0.7)", borderRadius: "6px", border: "1px dashed #30363d" }}>
          <span style={{ fontSize: "0.78rem", textTransform: "uppercase", letterSpacing: "1px", color: "#8b949e", fontWeight: "700" }}>REPORTED FAILURE:</span>
          <p style={{ margin: "6px 0 0 0", fontSize: "0.92rem", color: "#e6edf3", lineHeight: "1.5" }}>
            {pcb.failure_description || "None reported"}
          </p>
        </div>
      </div>

      {/* Grid: Diagnosis & Repairs */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px", marginBottom: "24px" }}>
        
        {/* Diagnosis Card */}
        <div style={{ backgroundColor: "#161b22", border: "1px solid #30363d", borderRadius: "8px", padding: "20px" }}>
          <h4 style={{ margin: "0 0 16px 0", color: "#58a6ff", fontSize: "1.08rem", display: "flex", alignItems: "center", gap: "8px" }}>
            <span>🩺</span> Diagnosis ({pcb.diagnoses ? pcb.diagnoses.length : 0})
          </h4>

          <div style={{ display: "flex", flexDirection: "column", gap: "12px", marginBottom: "18px", maxHeight: "260px", overflowY: "auto", paddingRight: "6px" }}>
            {(!pcb.diagnoses || pcb.diagnoses.length === 0) ? (
              <p style={{ color: "#6e7681", fontSize: "0.85rem", margin: 0 }}>No diagnosis logged yet.</p>
            ) : (
              pcb.diagnoses.map((d) => (
                <div key={d.id} style={{ backgroundColor: "#0d1117", border: "1px solid #21262d", borderRadius: "6px", padding: "14px" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "8px" }}>
                    <strong style={{ color: "#58a6ff", fontSize: "0.92rem", marginRight: "auto" }}>{d.technician}</strong>
                    <span style={{ color: "#8b949e", fontSize: "0.78rem" }}>{d.diagnosis_date ? String(d.diagnosis_date).split("T")[0] : ""}</span>
                    <div style={{ display: "flex", alignItems: "center", gap: "6px", flexShrink: 0 }}>
                    {!pcb.is_archived && (
                      <button type="button" onClick={() => {
                        setEditingDiagnosisId(d.id);
                        setDiagnosisEditForm({
                          technician: d.technician || "",
                          fault_found: d.fault_found || d.findings || "",
                          recommended_action: d.recommended_action || d.recommendation || "",
                          diagnosis_date: d.diagnosis_date ? String(d.diagnosis_date).split("T")[0] : "",
                        });
                      }} style={smallEditButton} title="Edit diagnosis" aria-label="Edit diagnosis">
                        {editingDiagnosisId === d.id ? <Pencil size={16} aria-label="Editing diagnosis" /> : <Pencil size={16} aria-label="Edit diagnosis" />}
                      </button>
                    )}
                    {user?.role === "admin" && !pcb.is_archived && (
                      <button
                        type="button"
                        disabled={deletingDiagnosisId === d.id}
                        onClick={() => handleDeleteDiagnosis(d.id)}
                        title="Delete diagnosis"
                        aria-label="Delete diagnosis"
                        style={{ ...smallEditButton, color: "#fecaca", borderColor: "#7f1d1d" }}
                      >
                        {deletingDiagnosisId === d.id ? "..." : <Trash2 size={16} aria-label="Delete diagnosis" />}
                      </button>
                    )}
                    </div>
                  </div>
                  {editingDiagnosisId === d.id && !pcb.is_archived && (
                    <form onSubmit={handleSaveDiagnosisEdit} style={{ display: "flex", flexDirection: "column", gap: "8px", marginBottom: "12px" }}>
                      <input required type="date" aria-label="Diagnosis date" style={inputStyle} value={diagnosisEditForm.diagnosis_date || ""} onChange={(e) => setDiagnosisEditForm({ ...diagnosisEditForm, diagnosis_date: e.target.value })} />
                      <input required aria-label="Diagnosis technician" style={inputStyle} placeholder="Technician Name" value={diagnosisEditForm.technician || ""} onChange={(e) => setDiagnosisEditForm({ ...diagnosisEditForm, technician: e.target.value })} />
                      <textarea required aria-label="Diagnostic findings" style={inputStyle} placeholder="Diagnostic Findings" value={diagnosisEditForm.fault_found || ""} onChange={(e) => setDiagnosisEditForm({ ...diagnosisEditForm, fault_found: e.target.value })} />
                      <textarea aria-label="Recommended action" style={inputStyle} placeholder="Recommended Action (optional)" value={diagnosisEditForm.recommended_action || ""} onChange={(e) => setDiagnosisEditForm({ ...diagnosisEditForm, recommended_action: e.target.value })} />
                      <div style={{ display: "flex", gap: "8px" }}>
                        <button type="submit" disabled={savingDiagnosisEdit} style={btnSuccess(savingDiagnosisEdit)}>{savingDiagnosisEdit ? "Saving..." : "Save"}</button>
                        <button type="button" disabled={savingDiagnosisEdit} style={smallEditButton} onClick={() => { setEditingDiagnosisId(null); setDiagnosisEditForm({}); }}>Cancel</button>
                      </div>
                    </form>
                  )}
                  <p style={{ margin: "0 0 8px 0", fontSize: "0.88rem", color: "#e6edf3", textAlign: "center", lineHeight: "1.4" }}>
                    {d.fault_found || d.findings}
                    {d.technician && (
                      <span style={{ color: "#8b949e", fontSize: "0.8rem", fontWeight: "normal" }}>
                        {" "}(by {d.technician})
                      </span>
                    )}
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

          {pcb.is_archived ? lockedNotice : (
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
                <button type="submit" disabled={savingDiag} style={btnSuccess(savingDiag)}>
                  {savingDiag ? "Adding..." : "+ Add Diagnosis"}
                </button>
              </div>
            </form>
          )}
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
                  <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "8px" }}>
                    <strong style={{ color: "#f0883e", fontSize: "0.92rem", marginRight: "auto" }}>{r.technician}</strong>
                    <span style={{ color: "#8b949e", fontSize: "0.78rem" }}>{r.repair_date ? String(r.repair_date).split("T")[0] : ""}</span>
                    <div style={{ display: "flex", alignItems: "center", gap: "6px", flexShrink: 0 }}>
                    {!pcb.is_archived && (
                      <button type="button" onClick={() => {
                        setEditingRepairId(r.id);
                        setRepairEditForm({
                          technician: r.technician || "",
                          actions_taken: r.actions_taken || r.action || "",
                          components_replaced: r.components_replaced || r.components_rep || "",
                          repair_date: r.repair_date ? String(r.repair_date).split("T")[0] : "",
                        });
                      }} style={smallEditButton} title="Edit repair" aria-label="Edit repair">
                        {editingRepairId === r.id ? <Pencil size={16} aria-label="Editing repair" /> : <Pencil size={16} aria-label="Edit repair" />}
                      </button>
                    )}
                    {user?.role === "admin" && !pcb.is_archived && (
                      <button
                        type="button"
                        disabled={deletingRepairId === r.id}
                        onClick={() => handleDeleteRepair(r.id)}
                        title="Delete repair"
                        aria-label="Delete repair"
                        style={{ ...smallEditButton, color: "#fecaca", borderColor: "#7f1d1d" }}
                      >
                        {deletingRepairId === r.id ? "..." : <Trash2 size={16} aria-label="Delete repair" />}
                      </button>
                    )}
                    </div>
                  </div>
                  {editingRepairId === r.id && !pcb.is_archived && (
                    <form onSubmit={handleSaveRepairEdit} style={{ display: "flex", flexDirection: "column", gap: "8px", marginBottom: "12px" }}>
                      <input required type="date" aria-label="Repair date" style={inputStyle} value={repairEditForm.repair_date || ""} onChange={(e) => setRepairEditForm({ ...repairEditForm, repair_date: e.target.value })} />
                      <input required aria-label="Repair technician" style={inputStyle} placeholder="Technician Name" value={repairEditForm.technician || ""} onChange={(e) => setRepairEditForm({ ...repairEditForm, technician: e.target.value })} />
                      <textarea required aria-label="Actions taken" style={inputStyle} placeholder="Actions Taken" value={repairEditForm.actions_taken || ""} onChange={(e) => setRepairEditForm({ ...repairEditForm, actions_taken: e.target.value })} />
                      <textarea aria-label="Components replaced" style={inputStyle} placeholder="Components Replaced (optional)" value={repairEditForm.components_replaced || ""} onChange={(e) => setRepairEditForm({ ...repairEditForm, components_replaced: e.target.value })} />
                      <div style={{ display: "flex", gap: "8px" }}>
                        <button type="submit" disabled={savingRepairEdit} style={btnSuccess(savingRepairEdit)}>{savingRepairEdit ? "Saving..." : "Save"}</button>
                        <button type="button" disabled={savingRepairEdit} style={smallEditButton} onClick={() => { setEditingRepairId(null); setRepairEditForm({}); }}>Cancel</button>
                      </div>
                    </form>
                  )}
                  <p style={{ margin: "0 0 8px 0", fontSize: "0.88rem", color: "#e6edf3", textAlign: "center", lineHeight: "1.4" }}>
                    {r.actions_taken || r.action}
                    {r.technician && (
                      <span style={{ color: "#8b949e", fontSize: "0.8rem", fontWeight: "normal" }}>
                        {" "}(by {r.technician})
                      </span>
                    )}
                  </p>
                  {(r.components_replaced || r.components_rep) && (
                    <div style={{ fontSize: "0.82rem", color: "#8b949e", textAlign: "center", borderTop: "1px solid #21262d", paddingTop: "6px" }}>
                      Replaced: <span style={{ color: "#d29922" }}>{r.components_replaced || r.components_rep}</span>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>

          {pcb.is_archived ? lockedNotice : (
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
                <button type="submit" disabled={savingRepair} style={btnSuccess(savingRepair)}>
                  {savingRepair ? "Adding..." : "+ Add Repair"}
                </button>
              </div>
            </form>
          )}
        </div>

      </div>

      {/* Tests Card */}
      <div style={{ backgroundColor: "#161b22", border: "1px solid #30363d", borderRadius: "8px", padding: "20px", marginBottom: "24px" }}>
        <h4 style={{ margin: "0 0 16px 0", color: "#3fb950", fontSize: "1.08rem", display: "flex", alignItems: "center", gap: "8px" }}>
          <span>✅</span> Tests ({pcb.tests ? pcb.tests.length : 0})
        </h4>

        <div style={{ display: "flex", flexDirection: "column", gap: "12px", marginBottom: "18px", maxHeight: "260px", overflowY: "auto", paddingRight: "6px" }}>
          {(!pcb.tests || pcb.tests.length === 0) ? (
            <p style={{ color: "#6e7681", fontSize: "0.85rem", margin: 0 }}>No tests executed yet.</p>
          ) : (
            pcb.tests.map((t) => {
              const isPassed = (t.result || "").toUpperCase() === "PASSED";
              const locked = isTestLocked(t);
              return (
                <div key={t.id} style={{ backgroundColor: "#0d1117", border: "1px solid #21262d", borderRadius: "6px", padding: "16px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                      <strong style={{ color: "#3fb950", fontSize: "0.95rem" }}>{t.tester || t.technician}</strong>
                      {locked && (
                        <span style={{
                          backgroundColor: "#7c2d12",
                          color: "#fdba74",
                          border: "1px solid #ea580c",
                          padding: "2px 6px",
                          borderRadius: "4px",
                          fontSize: "0.7rem",
                          fontWeight: "700"
                        }}>
                          🔒 Locked (&gt;1 yr)
                        </span>
                      )}
                    </div>
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
                  {editingTestId === t.id ? (
                    <form onSubmit={handleSaveTestEdit} style={{ display: "flex", flexDirection: "column", gap: "8px", margin: "12px 0" }}>
                      <label style={{ color: "#8b949e", fontSize: "0.8rem" }}>Test Date</label>
                      <input
                        required
                        type="date"
                        style={inputStyle}
                        value={testEditForm.test_date || ""}
                        onChange={(e) => setTestEditForm({ ...testEditForm, test_date: e.target.value })}
                      />
                      <input
                        required
                        style={inputStyle}
                        placeholder="Tester / Technician Name"
                        value={testEditForm.tester || ""}
                        onChange={(e) => setTestEditForm({ ...testEditForm, tester: e.target.value })}
                      />
                      <input
                        required
                        style={inputStyle}
                        placeholder="Test Type"
                        value={testEditForm.test_type || ""}
                        onChange={(e) => setTestEditForm({ ...testEditForm, test_type: e.target.value })}
                      />
                      <select
                        required
                        style={inputStyle}
                        value={testEditForm.result || ""}
                        onChange={(e) => setTestEditForm({ ...testEditForm, result: e.target.value })}
                      >
                        <option value="" disabled>Select Result</option>
                        <option value="PASSED">PASSED</option>
                        <option value="FAILED">FAILED</option>
                      </select>
                      <textarea
                        style={inputStyle}
                        placeholder="Test Notes (optional)"
                        value={testEditForm.notes || ""}
                        onChange={(e) => setTestEditForm({ ...testEditForm, notes: e.target.value })}
                      />
                      <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
                        <button type="submit" disabled={savingTestEdit} style={btnSuccess(savingTestEdit)}>
                          {savingTestEdit ? "Saving..." : "Save Changes"}
                        </button>
                        <button
                          type="button"
                          disabled={savingTestEdit}
                          style={smallEditButton}
                          onClick={() => { setEditingTestId(null); setTestEditForm({}); }}
                        >
                          Cancel
                        </button>
                      </div>
                    </form>
                  ) : (!locked && !pcb.is_archived && (
                    <div style={{ display: "flex", justifyContent: "flex-end", margin: "8px 0" }}>
                      <button
                        type="button"
                        style={smallEditButton}
                        onClick={() => {
                          setEditingTestId(t.id);
                          setTestEditForm({
                            test_date: String(t.test_date || "").slice(0, 10),
                            tester: t.tester || t.technician || "",
                            test_type: t.test_type || "",
                            result: t.result || "",
                            notes: t.notes || "",
                          });
                        }}
                      >
                        <Pencil size={16} aria-label="Edit test" />
                      </button>
                    </div>
                  ))}
                  <div style={{ textAlign: "center", fontWeight: "700", color: "#f0f6fc", fontSize: "0.98rem", margin: "6px 0" }}>
                    {t.test_type}
                    {(t.tester || t.technician) && (
                      <span style={{ color: "#8b949e", fontSize: "0.8rem", fontWeight: "normal" }}>
                        {" "}(by {t.tester || t.technician})
                      </span>
                    )}
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

        {pcb.is_archived ? lockedNotice : (
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
              <option value="" disabled>Select Result</option>\n                      <option value="PASSED">PASSED</option>
              <option value="FAILED">FAILED</option>
            </select>
            <input 
              style={inputStyle} 
              placeholder="Test Notes (optional)" 
              value={testForm.notes} 
              onChange={(e) => setTestForm({ ...testForm, notes: e.target.value })} 
            />
            <div>
              <button type="submit" disabled={savingTest} style={btnSuccess(savingTest)}>
                {savingTest ? "Adding..." : "+ Add Test"}
              </button>
            </div>
          </form>
        )}
      </div>

      {/* Visual Inspection Images Section */}
      <div style={{ backgroundColor: "#161b22", border: "1px solid #30363d", borderRadius: "8px", padding: "20px" }}>
        <h4 style={{ margin: "0 0 16px 0", color: "#e6edf3", fontSize: "1.08rem", display: "flex", alignItems: "center", gap: "8px" }}>
          <span>📷</span> Inspection & Defect Images ({pcb.images ? pcb.images.length : 0})
        </h4>

        {pcb.is_archived ? lockedNotice : (
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
              style={btnSuccess(uploading)}
            >
              {uploading ? "Uploading..." : "+ Upload Image"}
            </button>
          </form>
        )}

        {/* Images Grid */}
        {(!pcb.images || pcb.images.length === 0) ? (
          <p style={{ color: "#6e7681", fontSize: "0.88rem", margin: 0 }}>No inspection images uploaded for this PCB yet.</p>
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))", gap: "16px" }}>
            {pcb.images.map((img) => {
              const matchedTest = (pcb.tests || []).find((t) => t.id === img.test_id);
              const isEditingImage = editingImageId === img.id;

              return (
                <div key={img.id} style={{ border: "1px solid #30363d", borderRadius: "6px", overflow: "hidden", backgroundColor: "#0d1117", display: "flex", flexDirection: "column", height: "100%" }}>
                  <a href={img.filename_path} target="_blank" rel="noreferrer">
                    <img
                      src={img.filename_path}
                      alt={img.category}
                      style={{ width: "100%", height: "140px", objectFit: "cover", display: "block" }}
                    />
                  </a>
                  <div style={{ padding: "10px", display: "flex", flexDirection: "column", flex: 1 }}>
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

                    {!pcb.is_archived && !isEditingImage && (
                      <div style={{ display: "flex", gap: "8px", marginTop: "auto", paddingTop: "10px" }}>
                        <button
                          type="button"
                          onClick={() => startImageEdit(img)}
                          title="Edit image"
                          aria-label="Edit image"
                          style={{ flex: 1, padding: "6px 8px", borderRadius: "4px", border: "1px solid #30363d", background: "#21262d", color: "#c9d1d9", cursor: "pointer" }}
                        >
                          <Pencil size={16} aria-label="Edit image" />
                        </button>
                        <button
                          type="button"
                          disabled={deletingImageId === img.id}
                          onClick={() => handleDeleteImage(img.id)}
                          title="Delete image"
                          aria-label="Delete image"
                          style={{ flex: 1, padding: "6px 8px", borderRadius: "4px", border: "1px solid #7f1d1d", background: "#450a0a", color: "#fecaca", cursor: "pointer" }}
                        >
                          {deletingImageId === img.id ? "Deleting..." : <Trash2 size={16} aria-label="Delete image" />}
                        </button>
                      </div>
                    )}

                    {isEditingImage && !pcb.is_archived && (
                      <form onSubmit={(e) => handleSaveImageEdit(e, img.id)} style={{ display: "grid", gap: "8px", marginTop: "12px" }}>
                        <label style={{ color: "#8b949e", fontSize: "0.78rem" }}>
                          Category
                          <select
                            value={imageEditForm.category}
                            onChange={(e) => setImageEditForm((current) => ({ ...current, category: e.target.value }))}
                            style={{ display: "block", width: "100%", marginTop: "4px", padding: "7px", background: "#161b22", color: "#c9d1d9", border: "1px solid #30363d", borderRadius: "4px" }}
                          >
                            <option value="before">Before</option>
                            <option value="during">During</option>
                            <option value="after">After</option>
                            <option value="defect">Defect</option>
                          </select>
                        </label>

                        <label style={{ color: "#8b949e", fontSize: "0.78rem" }}>
                          Technician
                          <input
                            value={imageEditForm.technician}
                            onChange={(e) => setImageEditForm((current) => ({ ...current, technician: e.target.value }))}
                            maxLength={255}
                            style={{ display: "block", width: "100%", boxSizing: "border-box", marginTop: "4px", padding: "7px", background: "#161b22", color: "#c9d1d9", border: "1px solid #30363d", borderRadius: "4px" }}
                          />
                        </label>

                        <label style={{ color: "#8b949e", fontSize: "0.78rem" }}>
                          Linked test (optional)
                          <select
                            value={imageEditForm.test_id}
                            onChange={(e) => setImageEditForm((current) => ({ ...current, test_id: e.target.value }))}
                            style={{ display: "block", width: "100%", marginTop: "4px", padding: "7px", background: "#161b22", color: "#c9d1d9", border: "1px solid #30363d", borderRadius: "4px" }}
                          >
                            <option value="">No linked test</option>
                            {(pcb.tests || []).map((test) => (
                              <option key={test.id} value={String(test.id)}>
                                #{test.id} — {test.test_type}
                              </option>
                            ))}
                          </select>
                        </label>

                        <label style={{ color: "#8b949e", fontSize: "0.78rem" }}>
                          Replacement image (required)
                          <input
                            type="file"
                            accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp"
                            required
                            onChange={(e) => setImageEditFile(e.target.files?.[0] || null)}
                            style={{ display: "block", width: "100%", boxSizing: "border-box", marginTop: "4px", color: "#c9d1d9", fontSize: "0.75rem" }}
                          />
                        </label>

                        <div style={{ display: "flex", gap: "8px" }}>
                          <button
                            type="submit"
                            disabled={savingImageEdit}
                            style={{ flex: 1, padding: "7px", borderRadius: "4px", border: "1px solid #166534", background: "#14532d", color: "#dcfce7", cursor: "pointer" }}
                          >
                            {savingImageEdit ? "Saving..." : "Save"}
                          </button>
                          <button
                            type="button"
                            disabled={savingImageEdit}
                            onClick={cancelImageEdit}
                            style={{ flex: 1, padding: "7px", borderRadius: "4px", border: "1px solid #30363d", background: "#21262d", color: "#c9d1d9", cursor: "pointer" }}
                          >
                            Cancel
                          </button>
                        </div>
                      </form>
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
