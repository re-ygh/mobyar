// Simple API helper (Fetch wrapper)
// ------------------------------------------------------------
// All API calls go through this file so we can:
// - attach Authorization header
// - unify error handling
// - change base URL easily
// ------------------------------------------------------------

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

export function getToken() {
  return localStorage.getItem("mobyar_token");
}

export function setToken(token) {
  localStorage.setItem("mobyar_token", token);
}

export function clearToken() {
  localStorage.removeItem("mobyar_token");
}

export async function apiRequest(path, { method = "GET", body = null } = {}) {
  const headers = {
    "Content-Type": "application/json",
  };

  const token = getToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : null,
  });

  // Try to parse JSON response
  let data = null;
  const contentType = res.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    data = await res.json();
  } else {
    data = await res.text();
  }

  if (!res.ok) {
    // FastAPI usually returns { detail: "..." }
    const msg = (data && data.detail) ? data.detail : (typeof data === "string" ? data : "Request failed");
    throw new Error(msg);
  }

  return data;
}

// Auth
export async function login(phone, password) {
  return apiRequest("/auth/login", { method: "POST", body: { phone, password } });
}

export async function getMe() {
  return apiRequest("/auth/me");
}

// Data helpers used by pages
export async function fetchCategories() {
  return apiRequest("/categories");
}

export async function fetchProducts(includeInactive = false) {
  const q = includeInactive ? "?include_inactive=true" : "";
  return apiRequest(`/products${q}`);
}

export async function fetchServices(includeInactive = false) {
  const q = includeInactive ? "?include_inactive=true" : "";
  return apiRequest(`/services${q}`);
}

export async function fetchCustomers() {
  return apiRequest("/users/customers");
}

export async function fetchCustomerPhones(customerId) {
  const q = customerId ? `?customer_id=${customerId}` : "";
  return apiRequest(`/users/customer-phones${q}`);
}

// Sales
export async function createSale(customerId) {
  return apiRequest("/sales", { method: "POST", body: { customer_id: customerId || null } });
}

export async function getSale(saleId) {
  return apiRequest(`/sales/${saleId}`);
}

export async function addSaleItem(saleId, productId, quantity) {
  return apiRequest(`/sales/${saleId}/items`, { method: "POST", body: { product_id: productId, quantity } });
}

export async function removeSaleItem(saleId, productId) {
  return apiRequest(`/sales/${saleId}/items/${productId}`, { method: "DELETE" });
}

export async function finalizeSale(saleId) {
  return apiRequest(`/sales/${saleId}/finalize`, { method: "POST" });
}

// Repairs
export async function createRepair({ customer_id, phone_id, service_id, notes }) {
  return apiRequest("/repairs", { method: "POST", body: { customer_id, phone_id, service_id, notes } });
}

export async function listRepairs(status = "") {
  const q = status ? `?status_filter=${encodeURIComponent(status)}` : "";
  return apiRequest(`/repairs${q}`);
}

export async function updateRepairStatus(repairId, status) {
  return apiRequest(`/repairs/${repairId}/status`, { method: "PATCH", body: { status } });
}

// Reports
export async function reportDailySales(dateFrom = "", dateTo = "") {
  const params = new URLSearchParams();
  if (dateFrom) params.set("date_from", dateFrom);
  if (dateTo) params.set("date_to", dateTo);
  const q = params.toString() ? `?${params.toString()}` : "";
  return apiRequest(`/reports/daily-sales${q}`);
}

export async function reportLowStock(threshold = 5) {
  return apiRequest(`/reports/low-stock?threshold=${threshold}`);
}

export async function reportOpenRepairs() {
  return apiRequest(`/reports/open-repairs`);
}
