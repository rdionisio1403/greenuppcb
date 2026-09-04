export async function getPCBs(q = "") {
  const url = q ? `/pcbs?q=${encodeURIComponent(q)}` : "/pcbs";
  const response = await fetch(url);
  if (!response.ok) throw new Error("Could not load PCBs");
  return response.json();
}

export async function getPCB(id) {
  const response = await fetch(`/pcbs/${id}`);
  if (!response.ok) throw new Error("Could not load PCB details");
  return response.json();
}

export async function createPCB(data) {
  const response = await fetch("/pcbs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || "Could not create PCB");
  }
  return response.json();
}

export async function addDiagnosis(pcbId, data) {
  const response = await fetch(`/pcbs/${pcbId}/diagnoses`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error("Could not add diagnosis");
  return response.json();
}

export async function addRepair(pcbId, data) {
  const response = await fetch(`/pcbs/${pcbId}/repairs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error("Could not add repair");
  return response.json();
}

export async function addTest(pcbId, data) {
  const response = await fetch(`/pcbs/${pcbId}/tests`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error("Could not add test");
  return response.json();
}

export async function getPCBImages(pcbId) {
  const response = await fetch(`/pcbs/${pcbId}/images`);
  if (!response.ok) throw new Error("Could not load PCB images");
  return response.json();
}

export async function uploadPCBImage(pcbId, category, file) {
  const formData = new FormData();
  formData.append("category", category);
  formData.append("file", file);

  const response = await fetch(`/pcbs/${pcbId}/images`, {
    method: "POST",
    body: formData,
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || "Could not upload image");
  }
  return response.json();
}
