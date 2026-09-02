const API_URL = import.meta.env.VITE_API_URL || "";

export async function getPCBs() {
  const response = await fetch(`${API_URL}/pcbs`);
  if (!response.ok) throw new Error("Could not load PCBs");
  return response.json();
}

export async function getPCB(id) {
  const response = await fetch(`${API_URL}/pcbs/${id}`);
  if (!response.ok) throw new Error("Could not load PCB details");
  return response.json();
}

export async function createPCB(data) {
  const response = await fetch(`${API_URL}/pcbs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error("Could not create PCB");
  return response.json();
}

export async function addDiagnosis(pcbId, data) {
  const response = await fetch(`${API_URL}/pcbs/${pcbId}/diagnoses`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error("Could not add diagnosis");
  return response.json();
}

export async function addRepair(pcbId, data) {
  const response = await fetch(`${API_URL}/pcbs/${pcbId}/repairs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error("Could not add repair");
  return response.json();
}

export async function addTest(pcbId, data) {
  const response = await fetch(`${API_URL}/pcbs/${pcbId}/tests`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error("Could not add test");
  return response.json();
}
