export type RiskLevel = "RED" | "YELLOW" | "GREEN";

export interface ProductSummary {
  id: string;
  name: string;
  bank: string;
  category: string;
  headline_rate: string;
  description: string;
}

export interface ProductCondition {
  id: string;
  severity: "RED" | "YELLOW";
  field: string;
  operator: string;
  threshold: number;
  headline: string;
  summary_lines: string[];
  basis_clause: string;
  basis_source: string;
}

export interface Product extends ProductSummary {
  base_rate: number;
  max_preferential_rate: number;
  min_period_months: number;
  risk_conditions: ProductCondition[];
}

export interface UserProfile {
  id: string;
  display_name: string;
  monthly_income: number;
  emergency_fund: number;
  monthly_transit_count: number;
  monthly_taxi_count: number;
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
