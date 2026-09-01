import React, { useEffect, useState } from "react";
import { getPCBs } from "../api/pcbs";
import { Link } from "react-router-dom";

export default function PCBList() {
  const [pcbs, setPcbs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    getPCBs()
      .then(setPcbs)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p>Yükleniyor...</p>;
  if (error) return <p style={{ color: "red" }}>Hata: {error}</p>;

return (
    <div>
      <h3>Kayıtlı PCB Kartları</h3>
      <table style={{ width: "100%", borderCollapse: "collapse", marginTop: "10px" }} border="1" cellPadding="8">
        <thead>
          <tr style={{ background: "#f2f2f2" }}>
            <th>ID</th>
            <th>Referans No</th>
            <th>Müşteri</th>
            <th>Ekipman</th>
            <th>Durum</th>
            <th>Tarih</th>
            <th>İşlem</th>
          </tr>
        </thead>
        <tbody>
{pcbs.length === 0 ? (
            <tr><td colSpan="7" style={{ textAlign: "center" }}>Henüz kayıtlı PCB yok.</td></tr>
          ) : (
            pcbs.map((pcb) => (
              <tr key={pcb.id}>
                <td>{pcb.id}</td>
                <td><strong>{pcb.internal_reference}</strong></td>
                <td>{pcb.customer_name}</td>
                <td>{pcb.equipment}</td>
                <td><span style={{ padding: "3px 8px", borderRadius: "4px", background: "#e0f2fe", color: "#0369a1" }}>{pcb.status}</span></td>
                <td>{pcb.date_received}</td>
                <td><Link to={`/pcbs/${pcb.id}`}>Detay Görüntüle</Link></td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
