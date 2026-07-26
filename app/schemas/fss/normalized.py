from pydantic import BaseModel


class NormalizedDeposit(BaseModel):
    """예금 baseList+optionList를 fin_co_no+fin_prdt_cd로 조인한 결과."""

    fin_co_no: str
    fin_prdt_cd: str
    bank_name: str
    product_name: str
    join_way: str
    max_limit: int | None
    min_rate: float | None
    max_rate: float | None  # 우대금리 포함 최고금리
    terms_months: list[int]


class NormalizedSaving(NormalizedDeposit):
    reserve_types: list[str]  # 정액적립식 / 자유적립식


class NormalizedMortgageLoan(BaseModel):
    fin_co_no: str
    fin_prdt_cd: str
    bank_name: str
    product_name: str
    join_way: str
    loan_limit: str
    early_repay_fee: str
    min_rate: float | None
    max_rate: float | None
    avg_rate: float | None
    repay_types: list[str]


class NormalizedRentHouseLoan(NormalizedMortgageLoan):
    pass


class NormalizedCreditLoan(BaseModel):
    fin_co_no: str
    fin_prdt_cd: str
    bank_name: str
    product_name: str
    join_way: str
    cb_name: str
    best_grade_rate: float | None  # 최우수 신용구간 금리(최저)
    worst_grade_rate: float | None  # 최저 신용구간 금리(최고)
    avg_rate: float | None


class NormalizedBusinessLoan(BaseModel):
    fin_co_no: str
    fin_prdt_cd: str
    bank_name: str
    product_name: str
    join_way: str
    use_way: str
    loan_limit: str
    min_rate: float | None
    max_rate: float | None
    avg_rate: float | None


class NormalizedCompany(BaseModel):
    fin_co_no: str
    bank_name: str
    homepage_url: str
    call_center: str
    areas: list[str]
