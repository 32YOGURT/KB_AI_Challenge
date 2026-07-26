from pydantic import BaseModel


class InstitutionBalance(BaseModel):
    org_code: str
    total_balance: float
    is_over_protection_limit: bool


class MaturityItem(BaseModel):
    org_code: str
    account_num: str
    prod_name: str
    exp_date: str


class AssetDistributionSignal(BaseModel):
    """금융사별 자산 분포 & 만기 범용 집계. 예금자보호 초과/만기관리 판단에 재사용."""

    by_institution: list[InstitutionBalance]
    upcoming_maturities: list[MaturityItem]
