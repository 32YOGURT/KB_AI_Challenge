import type {
  AskResponse,
  CatalogProduct,
  CheckResponse,
  PresignedDocument,
  UserProfile,
  UserSignals,
} from "./types";

// 브라우저는 공개 URL로, Next.js 서버(서버 컴포넌트)는 도커 내부 네트워크로 백엔드를 부른다.
// 서버에서까지 공개 도메인으로 나가면 같은 호스트 안인데 DNS/TLS/리버스프록시를 한 바퀴 돌고,
// 그 경로가 준비되기 전(부팅 직후 등)엔 SSR이 통째로 실패한다.
const PUBLIC_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
const INTERNAL_BASE_URL = process.env.INTERNAL_API_BASE_URL ?? PUBLIC_BASE_URL;
const API_BASE_URL = typeof window === "undefined" ? INTERNAL_BASE_URL : PUBLIC_BASE_URL;

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

export function askQuestion(
  productId: string,
  userId: string,
  question: string,
  searchQuery?: string,
): Promise<AskResponse> {
  return request<AskResponse>("/api/ask", {
    method: "POST",
    body: JSON.stringify({
      product_id: productId,
      user_id: userId,
      question,
      search_query: searchQuery ?? null,
    }),
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

/** <a href>로 바로 열 수 있는 원문 PDF 주소. 서버가 presigned URL로 리다이렉트한다. */
export function documentOpenUrl(key: string): string {
  return `${PUBLIC_BASE_URL}/api/documents/open?key=${encodeURIComponent(key)}`;
}

export function fetchCatalog(productType?: string): Promise<CatalogProduct[]> {
  const query = productType ? `?product_type=${encodeURIComponent(productType)}` : "";
  return request<CatalogProduct[]>(`/api/catalog/products${query}`);
}
