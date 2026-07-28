export type RiskLevel = "RED" | "YELLOW" | "GREEN";

export interface UserProfile {
  id: string;
  display_name: string;
}

export interface RiskBasis {
  clause: string;
  source: string;
}

export interface RiskPoint {
  text: string;
  basis: RiskBasis | null;
}

export interface CheckResponse {
  product_id: string;
  product_name: string;
  user_id: string;
  risk_level: RiskLevel;
  points: RiskPoint[];
}

// app/schemas/catalog.py 미러링 — 크롤러가 만드는 상품 카탈로그 한 건.
export interface CatalogProduct {
  product_id: string;
  bank: string;
  name: string;
  category: string;
  sub_category: string;
  source_url: string;
}
