import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { getPCB, addDiagnosis, addRepair, addTest } from "../api/pcbs";

export default function PCBDetail() {
  const { id } = useParams();
  const [pcb, setPcb] = useState(null);
  const [loading, setLoading] = useState(true);

  // Form State'leri
  const [diagForm, setDiagForm] = useState({ technician: "", fault_found: "", recommended_action: "", diagnosis_date: new Date().toISOString().split("T")[0] });
  const [repairForm, setRepairForm] = useState({ technician: "", actions_taken: "", components_replaced: "", repair_date: new Date().toISOString().split("T")[0] });
  const [testForm, setTestForm] = useState({ technician: "", test_type: "", result: "PASSED", test_date: new Date().toISOString().split("T")[0] });

  const loadData = () => {
    getPCB(id).then(setPcb).finally(() => setLoading(false));
  };

useEffect(() => { loadData(); }, [id]);

  if (loading) return <p>Yükleniyor...</p>;
  if (!pcb) return <p>PCB bulunamadı.</p>;

  return (
    <div>
      <Link to="/">← Listeye Dön</Link>
      <div style={{ background: "#f8fafc", padding: "15px", borderRadius: "6px", margin: "15px 0" }}>
        <h2>{pcb.internal_reference} ({pcb.equipment})</h2>
        <p><strong>Müşteri:</strong> {pcb.customer_name} | <strong>Durum:</strong> {pcb.status} | <strong>Kayıt:</strong> {pcb.date_received}</p>
        <p><strong>Arıza Tanımı:</strong> {pcb.failure_description}</p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "15px" }}>
        {/* Diagnoses */}
        <div style={{ border: "1px solid #ddd", padding: "10px", borderRadius: "6px" }}>
          <h4>🩺 Teşhisler ({pcb.diagnoses?.length || 0})</h4>
          <ul>
            {pcb.diagnoses?.map((d) => (
              <li key={d.id}><strong>{d.fault_found}</strong> ({d.technician})</li>
            ))}
          </ul>
          <form onSubmit={async (e) => { e.preventDefault(); await addDiagnosis(id, diagForm); loadData(); }}>
            <input required placeholder="Teknisyen" value={diagForm.technician} onChange={(e) => setDiagForm({ ...diagForm, technician: e.target.value })} style={{ width: "90%", marginBottom: "5px" }} />
            <input required placeholder="Tespit Edilen Arıza" value={diagForm.fault_found} onChange={(e) => setDiagForm({ ...diagForm, fault_found: e.target.value })} style={{ width: "90%", marginBottom: "5px" }} />
            <button type="submit">Teşhis Ekle</button>
          </form>
        </div>

{/* Repairs */}
        <div style={{ border: "1px solid #ddd", padding: "10px", borderRadius: "6px" }}>
          <h4>🔧 Onarımlar ({pcb.repairs?.length || 0})</h4>
          <ul>
            {pcb.repairs?.map((r) => (
              <li key={r.id}><strong>{r.actions_taken}</strong> ({r.technician})</li>
            ))}
          </ul>
          <form onSubmit={async (e) => { e.preventDefault(); await addRepair(id, repairForm); loadData(); }}>
            <input required placeholder="Teknisyen" value={repairForm.technician} onChange={(e) => setRepairForm({ ...repairForm, technician: e.target.value })} style={{ width: "90%", marginBottom: "5px" }} />
            <input required placeholder="Yapılan İşlem" value={repairForm.actions_taken} onChange={(e) => setRepairForm({ ...repairForm, actions_taken: e.target.value })} style={{ width: "90%", marginBottom: "5px" }} />
            <button type="submit">Onarım Ekle</button>
          </form>
        </div>

{/* Tests */}
        <div style={{ border: "1px solid #ddd", padding: "10px", borderRadius: "6px" }}>
          <h4>✅ Testler ({pcb.tests?.length || 0})</h4>
          <ul>
            {pcb.tests?.map((t) => (
              <li key={t.id}><strong>{t.test_type}:</strong> {t.result}</li>
            ))}
          </ul>
          <form onSubmit={async (e) => { e.preventDefault(); await addTest(id, testForm); loadData(); }}>
            <input required placeholder="Teknisyen" value={testForm.technician} onChange={(e) => setTestForm({ ...testForm, technician: e.target.value })} style={{ width: "90%", marginBottom: "5px" }} />
            <input required placeholder="Test Tipi" value={testForm.test_type} onChange={(e) => setTestForm({ ...testForm, test_type: e.target.value })} style={{ width: "90%", marginBottom: "5px" }} />
            <select value={testForm.result} onChange={(e) => setTestForm({ ...testForm, result: e.target.value })} style={{ width: "95%", marginBottom: "5px" }}>
              <option value="PASSED">PASSED</option>
              <option value="FAILED">FAILED</option>
            </select>
            <button type="submit">Test Ekle</button>
          </form>
        </div>
      </div>
    </div>
  );
}
