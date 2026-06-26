export async function apiGet(path) {
  const response = await fetch(path, { credentials: "include" });
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}

export async function apiPost(path, payload = {}) {
  const response = await fetch(path, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || "Request failed");
  return data;
}
