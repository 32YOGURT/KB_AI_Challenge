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


class DepositRateOption(BaseModel):
    """만기별 금리 옵션 한 줄."""

    term_months: int | None
    base_rate: float | None
    preferential_rate: float | None


class NormalizedDepositDetail(NormalizedDeposit):
    """리스트엔 없는 FSS 원문 텍스트(우대조건/유의사항 등) + 만기별 금리 전체."""

    mtrt_int: str
    spcl_cnd: str
    join_deny: str
    join_member: str
    etc_note: str
    rate_options: list[DepositRateOption]


class NormalizedSavingDetail(NormalizedSaving):
    mtrt_int: str
    spcl_cnd: str
    join_deny: str
    join_member: str
    etc_note: str
    rate_options: list[DepositRateOption]


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


class LoanRateOption(BaseModel):
    """상환방식/금리유형 조합별 금리 한 줄."""

    repay_type_nm: str
    lend_rate_type_nm: str
    lend_rate_min: float
    lend_rate_max: float
    lend_rate_avg: float | None


class NormalizedMortgageLoanDetail(NormalizedMortgageLoan):
    loan_inci_expn: str
    dly_rate: str
    rate_options: list[LoanRateOption]


class NormalizedRentHouseLoanDetail(NormalizedRentHouseLoan):
    loan_inci_expn: str
    dly_rate: str
    rate_options: list[LoanRateOption]


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


class CreditGradeRate(BaseModel):
    """신용점수 구간별 금리 한 줄. 구간이 가리키는 실제 점수 범위는 FSS 문서 확인이
    필요해 원본 필드명(예: crdt_grad_1)을 그대로 노출한다."""

    field: str
    rate: float


class NormalizedCreditLoanDetail(NormalizedCreditLoan):
    crdt_lend_rate_type_nm: str
    grade_rates: list[CreditGradeRate]


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


class NormalizedBusinessLoanDetail(NormalizedBusinessLoan):
    fin_prdt_type_nm: str
    loan_type: str
    loan_limit_detl: str
    join_deny_detl: str | None
    loan_term: str
    early_repay_fee: str
    loan_inci_expn: str
    dly_rate: str


class NormalizedCompany(BaseModel):
    fin_co_no: str
    bank_name: str
    homepage_url: str
    call_center: str
    areas: list[str]
