import type { CatalogProduct, CheckResponse, PresignedDocument, UserProfile } from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`${init?.method ?? "GET"} ${path} failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export function fetchUsers(): Promise<UserProfile[]> {
  return request<UserProfile[]>("/api/users");
}

export function checkProduct(productId: string, userId: string): Promise<CheckResponse> {
  return request<CheckResponse>("/api/check", {
    method: "POST",
    body: JSON.stringify({ product_id: productId, user_id: userId }),
  });
}

export function presignDocument(key: string): Promise<PresignedDocument> {
  return request<PresignedDocument>(`/api/documents/presign?key=${encodeURIComponent(key)}`);
}

export function fetchCatalog(productType?: string): Promise<CatalogProduct[]> {
  const query = productType ? `?product_type=${encodeURIComponent(productType)}` : "";
  return request<CatalogProduct[]>(`/api/catalog/products${query}`);
}
