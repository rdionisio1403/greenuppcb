// Using relative paths to route requests cleanly through Vite dev server proxy
import { apiFetch } from "./apiFetch";
export async function getPCBs(q = "", page = 1, limit = 10) {
  const params = new URLSearchParams();
  if (q && q.trim()) params.append("q", q.trim());
  params.append("page", page);
  params.append("limit", limit);

  const res = await apiFetch(`/pcbs?${params.toString()}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch PCBs: ${res.statusText}`);
  }
  return await res.json();
}

export async function getPCB(id) {
  const res = await apiFetch(`/pcbs/${id}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch PCB details: ${res.statusText}`);
  }
  return await res.json();
}

export async function createPCB(data) {
  const res = await apiFetch("/pcbs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    throw new Error(`Failed to create PCB: ${res.statusText}`);
  }
  return await res.json();
}

export async function addDiagnosis(pcbId, data) {
  const res = await apiFetch("/diagnoses", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...data, pcb_id: pcbId }),
  });
  if (!res.ok) {
    throw new Error(`Failed to add diagnosis: ${res.statusText}`);
  }
  return await res.json();
}

export async function addRepair(pcbId, data) {
  const res = await apiFetch("/repairs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...data, pcb_id: pcbId }),
  });
  if (!res.ok) {
    throw new Error(`Failed to add repair: ${res.statusText}`);
  }
  return await res.json();
}

export async function addTest(pcbId, data) {
  const res = await apiFetch("/tests", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...data, pcb_id: pcbId }),
  });
  if (!res.ok) {
    throw new Error(`Failed to add test: ${res.statusText}`);
  }
  return await res.json();
}

export async function uploadPCBImage(pcbId, formData) {
  const res = await apiFetch(`/images/upload/${pcbId}`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    throw new Error(`Failed to upload image: ${res.statusText}`);
  }
  return await res.json();
}
