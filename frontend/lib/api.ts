import type {
  CatalogProduct,
  CheckResponse,
  PresignedDocument,
  UserProfile,
  UserSignals,
} from "./types";

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

/** 마이데이터 표준 인가 흐름 그대로: 토큰을 발급받아 Bearer로 신호를 조회한다. */
export async function fetchUserSignals(userId: string): Promise<UserSignals> {
  const { access_token } = await request<{ access_token: string }>("/api/mydata/token", {
    method: "POST",
    body: JSON.stringify({ user_id: userId }),
  });
  return request<UserSignals>("/api/mydata/me", {
    headers: { Authorization: `Bearer ${access_token}` },
  });
}

export function presignDocument(key: string): Promise<PresignedDocument> {
  return request<PresignedDocument>(`/api/documents/presign?key=${encodeURIComponent(key)}`);
}

export function fetchCatalog(productType?: string): Promise<CatalogProduct[]> {
  const query = productType ? `?product_type=${encodeURIComponent(productType)}` : "";
  return request<CatalogProduct[]>(`/api/catalog/products${query}`);
}
