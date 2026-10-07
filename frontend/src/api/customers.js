import { apiFetch } from "./apiFetch";

export async function getCustomers() {
  const res = await apiFetch("/customers");
  if (!res.ok) {
    throw new Error(`Failed to fetch customers: ${res.statusText}`);
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
    throw new Error(`Failed to create customer: ${res.statusText}`);
  }
  return await res.json();
}
