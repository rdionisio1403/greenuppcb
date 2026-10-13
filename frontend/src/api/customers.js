import { apiFetch } from "./apiFetch";

async function readError(res, fallback) {
  try {
    const body = await res.json();
    if (typeof body.detail === "string") return body.detail;
    if (Array.isArray(body.detail)) {
      return body.detail.map((item) => item.msg).join("; ");
    }
  } catch {
    // Use fallback when the response has no JSON body.
  }
  return fallback;
}

export async function getCustomers() {
  const res = await apiFetch("/customers");
  if (!res.ok) {
    throw new Error(await readError(res, "Failed to fetch customers."));
  }
  return await res.json();
}

export async function createCustomer(data) {
  const res = await apiFetch("/customers", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    throw new Error(await readError(res, "Failed to create customer."));
  }
  return await res.json();
}

export async function updateCustomer(id, data) {
  const res = await apiFetch(`/customers/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    throw new Error(await readError(res, "Failed to update customer."));
  }
  return await res.json();
}

export async function deleteCustomer(id) {
  const res = await apiFetch(`/customers/${id}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    throw new Error(await readError(res, "Failed to delete customer."));
  }
}
