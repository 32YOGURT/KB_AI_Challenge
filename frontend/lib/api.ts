import type { CheckResponse, Product, ProductSummary, UserProfile } from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

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

export function fetchProducts(): Promise<ProductSummary[]> {
  return request<ProductSummary[]>("/api/products");
}

export function fetchProduct(productId: string): Promise<Product> {
  return request<Product>(`/api/products/${productId}`);
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
