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

export async function updatePCB(id, data) {
  const res = await apiFetch(`/pcbs/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to update PCB: ${res.statusText}`);
  }

  return await res.json();
}

export async function addDiagnosis(pcbId, data) {
  const res = await apiFetch(`/pcbs/${pcbId}/diagnoses`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    throw new Error(`Failed to add diagnosis: ${res.statusText}`);
  }
  return await res.json();
}

export async function addRepair(pcbId, data) {
  const res = await apiFetch(`/pcbs/${pcbId}/repairs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    throw new Error(`Failed to add repair: ${res.statusText}`);
  }
  return await res.json();
}

export async function addTest(pcbId, data) {
  const res = await apiFetch(`/pcbs/${pcbId}/tests`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    throw new Error(`Failed to add test: ${res.statusText}`);
  }
  return await res.json();
}

export async function updateTest(pcbId, testId, data) {
  const res = await apiFetch(`/pcbs/${pcbId}/tests/${testId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to update test: ${res.statusText}`);
  }
  return await res.json();
}

export async function uploadPCBImage(pcbId, formData) {
  const res = await apiFetch(`/pcbs/${pcbId}/images`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    throw new Error(`Failed to upload image: ${res.statusText}`);
  }
  return await res.json();
}


export async function updateDiagnosis(pcbId, diagnosisId, data) {
  const res = await apiFetch(`/pcbs/${pcbId}/diagnoses/${diagnosisId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to update diagnosis: ${res.statusText}`);
  }

  return await res.json();
}

export async function deleteDiagnosis(pcbId, diagnosisId) {
  const res = await apiFetch(`/pcbs/${pcbId}/diagnoses/${diagnosisId}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to delete diagnosis: ${res.statusText}`);
  }
}

export async function deleteRepair(pcbId, repairId) {
  const res = await apiFetch(`/pcbs/${pcbId}/repairs/${repairId}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to delete repair: ${res.statusText}`);
  }
}

export async function updateRepair(pcbId, repairId, data) {
  const res = await apiFetch(`/pcbs/${pcbId}/repairs/${repairId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to update repair: ${res.statusText}`);
  }

  return await res.json();
}


export async function replacePCBImage(pcbId, imageId, formData) {
  const res = await apiFetch(`/pcbs/${pcbId}/images/${imageId}`, {
    method: "PUT",
    body: formData,
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to update image: ${res.statusText}`);
  }
  return await res.json();
}

export async function deletePCBImage(pcbId, imageId) {
  const res = await apiFetch(`/pcbs/${pcbId}/images/${imageId}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to delete image: ${res.statusText}`);
  }
}
