export const session = {
  get(key) { try { return sessionStorage.getItem(`tablekeeper.${key}`); } catch { return null; } },
  set(key, value) { try { sessionStorage.setItem(`tablekeeper.${key}`, value); } catch { /* session continuity is best effort */ } },
  remove(key) { try { sessionStorage.removeItem(`tablekeeper.${key}`); } catch { /* private mode */ } }
};

export function token() { return session.get("token"); }
export function user() { try { return JSON.parse(session.get("user") || "null"); } catch { return null; } }
export function escapeHTML(value) {
  return String(value ?? "").replace(/[&<>"']/g, char => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char]);
}
export function api(path, options = {}) {
  const headers = { Accept: "application/json", ...(options.headers || {}) };
  if (token()) headers.Authorization = `Bearer ${token()}`;
  if (options.json !== undefined) headers["Content-Type"] = "application/json";
  return fetch(path, { method: options.method || "GET", headers, body: options.json === undefined ? undefined : JSON.stringify(options.json) });
}
export async function readResponse(response) {
  const value = await response.json();
  if (!response.ok) {
    const error = new Error(value?.error?.message || `Request refused (${response.status})`);
    error.status = response.status;
    error.code = value?.error?.code;
    throw error;
  }
  return value;
}
export function showMessage(target, testid, text, kind = "error") {
  const old = target.querySelector(`[data-testid="${testid}"]`);
  if (old) old.remove();
  if (!text) return;
  const node = document.createElement("p");
  node.className = `feedback feedback-${kind}`;
  node.dataset.testid = testid;
  node.setAttribute("role", kind === "error" ? "alert" : "status");
  node.textContent = text;
  target.append(node);
}
export function localToday() {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
}
export function labelFor(restaurant, id) {
  return restaurant?.tables?.find(table => table.id === id)?.label || id;
}
export function labelsFor(restaurant, ids) { return ids.map(id => labelFor(restaurant, id)); }
export function setKey(ids) { return [...ids].sort().join("\u001f"); }
export function makeKey() {
  if (globalThis.crypto?.randomUUID) return crypto.randomUUID();
  return `web-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}
