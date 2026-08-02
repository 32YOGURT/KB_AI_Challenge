export interface UserProfile {
  id: string;
  display_name: string;
  description: string;
}

// app/schemas/signals/* 미러링 — 마이데이터 목업에서 집계한 신호.
export interface LiquiditySignal {
  balance_amt: number;
  withdrawable_amt: number;
  recent_net_cash_flow: number;
  transaction_count: number;
}

export interface InstitutionBalance {
  org_code: string;
  total_balance: number;
  is_over_protection_limit: boolean;
}

export interface MaturityItem {
  org_code: string;
  account_num: string;
  prod_name: string;
  exp_date: string;
}

export interface AssetDistributionSignal {
  by_institution: InstitutionBalance[];
  upcoming_maturities: MaturityItem[];
}

export interface CategorySpend {
  category: string;
  count: number;
  total_amt: number;
}

export interface CardCategorySignal {
  by_category: CategorySpend[];
}

export interface UserSignals {
  user_id: string;
  liquidity: LiquiditySignal;
  asset_distribution: AssetDistributionSignal;
  card_category: CardCategorySignal;
}

export interface RiskBasis {
  clause: string;
  source: string;
  source_key: string; // 원문 PDF(MinIO object key). 재색인 전 조항은 빈 문자열
  page: number | null;
  quote: string | null; // 근거 원문 인용(검증 통과분만). null이면 하이라이팅 생략
}

export interface RiskPoint {
  type: "description" | "risk";
  text: string;
  detail: string;
  basis: RiskBasis | null;
}

export interface SuggestedQuestion {
  question: string;
  search_query: string; // 약관 어휘 기반 검색어. 그대로 /api/ask에 넘긴다
}

export interface CheckResponse {
  product_id: string;
  product_name: string;
  user_id: string;
  points: RiskPoint[];
  suggested_questions: SuggestedQuestion[];
}

export interface AskResponse {
  question: string;
  answer: string;
  basis: RiskBasis | null;
}

export interface PresignedDocument {
  url: string;
  expires_in: number;
}

// app/schemas/catalog.py 미러링 — 크롤러가 만드는 상품 카탈로그 한 건.
export interface CatalogProduct {
  product_id: string;
  bank: string;
  name: string;
  product_type: string; // 은행 무관 정규 분류
  category: string; // 은행 사이트 원문 분류
  sub_category: string;
  doc_key: string | null; // 원문 PDF(상품설명서 우선) object key
}
