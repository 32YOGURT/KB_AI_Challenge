import type {
  CheckResponse,
  NormalizedBusinessLoan,
  NormalizedBusinessLoanDetail,
  NormalizedCompany,
  NormalizedCreditLoan,
  NormalizedCreditLoanDetail,
  NormalizedDeposit,
  NormalizedDepositDetail,
  NormalizedMortgageLoan,
  NormalizedMortgageLoanDetail,
  NormalizedRentHouseLoan,
  NormalizedRentHouseLoanDetail,
  NormalizedSaving,
  NormalizedSavingDetail,
  UserProfile,
} from "./types";

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

export function fetchUsers(): Promise<UserProfile[]> {
  return request<UserProfile[]>("/api/users");
}

export function checkProduct(productId: string, userId: string): Promise<CheckResponse> {
  return request<CheckResponse>("/api/check", {
    method: "POST",
    body: JSON.stringify({ product_id: productId, user_id: userId }),
  });
}

export function fetchDeposits(): Promise<NormalizedDeposit[]> {
  return request<NormalizedDeposit[]>("/api/products/deposits");
}

export function fetchSavings(): Promise<NormalizedSaving[]> {
  return request<NormalizedSaving[]>("/api/products/savings");
}

export function fetchMortgageLoans(): Promise<NormalizedMortgageLoan[]> {
  return request<NormalizedMortgageLoan[]>("/api/products/mortgage-loans");
}

export function fetchRentHouseLoans(): Promise<NormalizedRentHouseLoan[]> {
  return request<NormalizedRentHouseLoan[]>("/api/products/rent-house-loans");
}

export function fetchCreditLoans(): Promise<NormalizedCreditLoan[]> {
  return request<NormalizedCreditLoan[]>("/api/products/credit-loans");
}

export function fetchBusinessLoans(): Promise<NormalizedBusinessLoan[]> {
  return request<NormalizedBusinessLoan[]>("/api/products/business-loans");
}

export function fetchCompanies(): Promise<NormalizedCompany[]> {
  return request<NormalizedCompany[]>("/api/products/companies");
}

export function fetchDepositDetail(finCoNo: string, finPrdtCd: string): Promise<NormalizedDepositDetail> {
  return request<NormalizedDepositDetail>(
    `/api/products/deposits/${encodeURIComponent(finCoNo)}/${encodeURIComponent(finPrdtCd)}`,
  );
}

export function fetchSavingDetail(finCoNo: string, finPrdtCd: string): Promise<NormalizedSavingDetail> {
  return request<NormalizedSavingDetail>(
    `/api/products/savings/${encodeURIComponent(finCoNo)}/${encodeURIComponent(finPrdtCd)}`,
  );
}

export function fetchMortgageLoanDetail(
  finCoNo: string,
  finPrdtCd: string,
): Promise<NormalizedMortgageLoanDetail> {
  return request<NormalizedMortgageLoanDetail>(
    `/api/products/mortgage-loans/${encodeURIComponent(finCoNo)}/${encodeURIComponent(finPrdtCd)}`,
  );
}

export function fetchRentHouseLoanDetail(
  finCoNo: string,
  finPrdtCd: string,
): Promise<NormalizedRentHouseLoanDetail> {
  return request<NormalizedRentHouseLoanDetail>(
    `/api/products/rent-house-loans/${encodeURIComponent(finCoNo)}/${encodeURIComponent(finPrdtCd)}`,
  );
}

export function fetchCreditLoanDetail(finCoNo: string, finPrdtCd: string): Promise<NormalizedCreditLoanDetail> {
  return request<NormalizedCreditLoanDetail>(
    `/api/products/credit-loans/${encodeURIComponent(finCoNo)}/${encodeURIComponent(finPrdtCd)}`,
  );
}

export function fetchBusinessLoanDetail(
  finCoNo: string,
  finPrdtCd: string,
): Promise<NormalizedBusinessLoanDetail> {
  return request<NormalizedBusinessLoanDetail>(
    `/api/products/business-loans/${encodeURIComponent(finCoNo)}/${encodeURIComponent(finPrdtCd)}`,
  );
}
