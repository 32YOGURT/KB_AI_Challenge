export type RiskLevel = "RED" | "YELLOW" | "GREEN";

export interface UserProfile {
  id: string;
  display_name: string;
}

export interface RiskBasis {
  clause: string;
  source: string;
}

export interface CheckResponse {
  product_id: string;
  product_name: string;
  user_id: string;
  risk_level: RiskLevel;
  headline: string;
  summary_lines: string[];
  basis: RiskBasis[];
}

// app/schemas/fss/normalized.py 미러링 — FSS baseList/optionList를 백엔드가 조인·정제한 결과.
export interface NormalizedDeposit {
  fin_co_no: string;
  fin_prdt_cd: string;
  bank_name: string;
  product_name: string;
  join_way: string;
  max_limit: number | null;
  min_rate: number | null;
  max_rate: number | null;
  terms_months: number[];
}

export interface NormalizedSaving extends NormalizedDeposit {
  reserve_types: string[];
}

export interface NormalizedMortgageLoan {
  fin_co_no: string;
  fin_prdt_cd: string;
  bank_name: string;
  product_name: string;
  join_way: string;
  loan_limit: string;
  early_repay_fee: string;
  min_rate: number | null;
  max_rate: number | null;
  avg_rate: number | null;
  repay_types: string[];
}

export type NormalizedRentHouseLoan = NormalizedMortgageLoan;

export interface NormalizedCreditLoan {
  fin_co_no: string;
  fin_prdt_cd: string;
  bank_name: string;
  product_name: string;
  join_way: string;
  cb_name: string;
  best_grade_rate: number | null;
  worst_grade_rate: number | null;
  avg_rate: number | null;
}

export interface NormalizedBusinessLoan {
  fin_co_no: string;
  fin_prdt_cd: string;
  bank_name: string;
  product_name: string;
  join_way: string;
  use_way: string;
  loan_limit: string;
  min_rate: number | null;
  max_rate: number | null;
  avg_rate: number | null;
}

export interface NormalizedCompany {
  fin_co_no: string;
  bank_name: string;
  homepage_url: string;
  call_center: string;
  areas: string[];
}
