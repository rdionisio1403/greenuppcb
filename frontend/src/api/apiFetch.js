export async function apiFetch(url, options = {}) {
  return fetch(url, {
    ...options,
    credentials: "include",
  });
}
