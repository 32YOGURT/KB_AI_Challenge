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

export interface DepositRateOption {
  term_months: number | null;
  base_rate: number | null;
  preferential_rate: number | null;
}

export interface NormalizedDepositDetail extends NormalizedDeposit {
  mtrt_int: string;
  spcl_cnd: string;
  join_deny: string;
  join_member: string;
  etc_note: string;
  rate_options: DepositRateOption[];
}

export interface NormalizedSavingDetail extends NormalizedSaving {
  mtrt_int: string;
  spcl_cnd: string;
  join_deny: string;
  join_member: string;
  etc_note: string;
  rate_options: DepositRateOption[];
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

export interface LoanRateOption {
  repay_type_nm: string;
  lend_rate_type_nm: string;
  lend_rate_min: number;
  lend_rate_max: number;
  lend_rate_avg: number | null;
}

export interface NormalizedMortgageLoanDetail extends NormalizedMortgageLoan {
  loan_inci_expn: string;
  dly_rate: string;
  rate_options: LoanRateOption[];
}

export interface NormalizedRentHouseLoanDetail extends NormalizedRentHouseLoan {
  loan_inci_expn: string;
  dly_rate: string;
  rate_options: LoanRateOption[];
}

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

export interface CreditGradeRate {
  field: string;
  rate: number;
}

export interface NormalizedCreditLoanDetail extends NormalizedCreditLoan {
  crdt_lend_rate_type_nm: string;
  grade_rates: CreditGradeRate[];
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

export interface NormalizedBusinessLoanDetail extends NormalizedBusinessLoan {
  fin_prdt_type_nm: string;
  loan_type: string;
  loan_limit_detl: string;
  join_deny_detl: string | null;
  loan_term: string;
  early_repay_fee: string;
  loan_inci_expn: string;
  dly_rate: string;
}

export interface NormalizedCompany {
  fin_co_no: string;
  bank_name: string;
  homepage_url: string;
  call_center: string;
  areas: string[];
}
