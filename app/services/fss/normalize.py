"""FSS(금융감독원) 원본 응답 정제.

카테고리별 baseList(상품 고정정보) + optionList(금리 옵션, 상품당 여러 행)를
fin_co_no+fin_prdt_cd로 조인해 프론트에 내려줄 상품 단위 레코드로 만든다.
"""

from collections import defaultdict
from collections.abc import Callable, Iterable
from typing import TypeVar

from app.schemas.fss.business_loan import Model as BusinessLoanSearchResponse
from app.schemas.fss.company import Model as CompanySearchResponse
from app.schemas.fss.credit_loan import Model as CreditLoanSearchResponse
from app.schemas.fss.deposit import Model as DepositSearchResponse
from app.schemas.fss.mortgage_loan import Model as MortgageLoanSearchResponse
from app.schemas.fss.normalized import (
    CreditGradeRate,
    DepositRateOption,
    LoanRateOption,
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
)
from app.schemas.fss.rent_house_loan import Model as RentHouseLoanSearchResponse
from app.schemas.fss.saving import Model as SavingSearchResponse

TOption = TypeVar("TOption")
TKey = TypeVar("TKey")

CREDIT_GRADE_FIELDS = (
    "crdt_grad_1",
    "crdt_grad_4",
    "crdt_grad_5",
    "crdt_grad_6",
    "crdt_grad_10",
    "crdt_grad_11",
    "crdt_grad_12",
    "crdt_grad_13",
)


def _group_by(options: Iterable[TOption], key_fn: Callable[[TOption], TKey]) -> dict[TKey, list[TOption]]:
    grouped: dict[TKey, list[TOption]] = defaultdict(list)
    for option in options:
        grouped[key_fn(option)].append(option)
    return grouped


def _product_key(item) -> tuple[str, str]:
    return (item.fin_co_no, item.fin_prdt_cd)


def normalize_deposits(response: DepositSearchResponse) -> list[NormalizedDeposit]:
    result = response.result
    options_by_product = _group_by(result.optionList, _product_key)

    normalized = []
    for base in result.baseList:
        options = options_by_product.get(_product_key(base), [])
        base_rates = [o.intr_rate for o in options if o.intr_rate is not None]
        best_rates = [o.intr_rate2 if o.intr_rate2 is not None else o.intr_rate for o in options]
        best_rates = [r for r in best_rates if r is not None]
        terms = sorted({int(o.save_trm) for o in options if o.save_trm.isdigit()})

        normalized.append(
            NormalizedDeposit(
                fin_co_no=base.fin_co_no,
                fin_prdt_cd=base.fin_prdt_cd,
                bank_name=base.kor_co_nm,
                product_name=base.fin_prdt_nm,
                join_way=base.join_way,
                max_limit=base.max_limit,
                min_rate=min(base_rates) if base_rates else None,
                max_rate=max(best_rates) if best_rates else None,
                terms_months=terms,
            )
        )
    return normalized


def normalize_deposit_detail(
    response: DepositSearchResponse, fin_co_no: str, fin_prdt_cd: str
) -> NormalizedDepositDetail | None:
    result = response.result
    base = next(
        (b for b in result.baseList if b.fin_co_no == fin_co_no and b.fin_prdt_cd == fin_prdt_cd), None
    )
    if base is None:
        return None

    options = [o for o in result.optionList if o.fin_co_no == fin_co_no and o.fin_prdt_cd == fin_prdt_cd]
    base_rates = [o.intr_rate for o in options if o.intr_rate is not None]
    best_rates = [o.intr_rate2 if o.intr_rate2 is not None else o.intr_rate for o in options]
    best_rates = [r for r in best_rates if r is not None]

    return NormalizedDepositDetail(
        fin_co_no=base.fin_co_no,
        fin_prdt_cd=base.fin_prdt_cd,
        bank_name=base.kor_co_nm,
        product_name=base.fin_prdt_nm,
        join_way=base.join_way,
        max_limit=base.max_limit,
        min_rate=min(base_rates) if base_rates else None,
        max_rate=max(best_rates) if best_rates else None,
        terms_months=sorted({int(o.save_trm) for o in options if o.save_trm.isdigit()}),
        mtrt_int=base.mtrt_int,
        spcl_cnd=base.spcl_cnd,
        join_deny=base.join_deny,
        join_member=base.join_member,
        etc_note=base.etc_note,
        rate_options=[
            DepositRateOption(
                term_months=int(o.save_trm) if o.save_trm.isdigit() else None,
                base_rate=o.intr_rate,
                preferential_rate=o.intr_rate2,
            )
            for o in options
        ],
    )


def normalize_savings(response: SavingSearchResponse) -> list[NormalizedSaving]:
    result = response.result
    options_by_product = _group_by(result.optionList, _product_key)

    normalized = []
    for base in result.baseList:
        options = options_by_product.get(_product_key(base), [])
        base_rates = [o.intr_rate for o in options if o.intr_rate is not None]
        best_rates = [o.intr_rate2 if o.intr_rate2 is not None else o.intr_rate for o in options]
        best_rates = [r for r in best_rates if r is not None]
        terms = sorted({int(o.save_trm) for o in options if o.save_trm.isdigit()})
        reserve_types = sorted({o.rsrv_type_nm for o in options})

        normalized.append(
            NormalizedSaving(
                fin_co_no=base.fin_co_no,
                fin_prdt_cd=base.fin_prdt_cd,
                bank_name=base.kor_co_nm,
                product_name=base.fin_prdt_nm,
                join_way=base.join_way,
                max_limit=base.max_limit,
                min_rate=min(base_rates) if base_rates else None,
                max_rate=max(best_rates) if best_rates else None,
                terms_months=terms,
                reserve_types=reserve_types,
            )
        )
    return normalized


def normalize_saving_detail(
    response: SavingSearchResponse, fin_co_no: str, fin_prdt_cd: str
) -> NormalizedSavingDetail | None:
    result = response.result
    base = next(
        (b for b in result.baseList if b.fin_co_no == fin_co_no and b.fin_prdt_cd == fin_prdt_cd), None
    )
    if base is None:
        return None

    options = [o for o in result.optionList if o.fin_co_no == fin_co_no and o.fin_prdt_cd == fin_prdt_cd]
    base_rates = [o.intr_rate for o in options if o.intr_rate is not None]
    best_rates = [o.intr_rate2 if o.intr_rate2 is not None else o.intr_rate for o in options]
    best_rates = [r for r in best_rates if r is not None]

    return NormalizedSavingDetail(
        fin_co_no=base.fin_co_no,
        fin_prdt_cd=base.fin_prdt_cd,
        bank_name=base.kor_co_nm,
        product_name=base.fin_prdt_nm,
        join_way=base.join_way,
        max_limit=base.max_limit,
        min_rate=min(base_rates) if base_rates else None,
        max_rate=max(best_rates) if best_rates else None,
        terms_months=sorted({int(o.save_trm) for o in options if o.save_trm.isdigit()}),
        reserve_types=sorted({o.rsrv_type_nm for o in options}),
        mtrt_int=base.mtrt_int,
        spcl_cnd=base.spcl_cnd,
        join_deny=base.join_deny,
        join_member=base.join_member,
        etc_note=base.etc_note,
        rate_options=[
            DepositRateOption(
                term_months=int(o.save_trm) if o.save_trm.isdigit() else None,
                base_rate=o.intr_rate,
                preferential_rate=o.intr_rate2,
            )
            for o in options
        ],
    )


def normalize_mortgage_loans(response: MortgageLoanSearchResponse) -> list[NormalizedMortgageLoan]:
    result = response.result
    options_by_product = _group_by(result.optionList, _product_key)

    normalized = []
    for base in result.baseList:
        options = options_by_product.get(_product_key(base), [])
        min_rates = [o.lend_rate_min for o in options]
        max_rates = [o.lend_rate_max for o in options]
        avg_rates = [o.lend_rate_avg for o in options if o.lend_rate_avg is not None]
        repay_types = sorted({o.rpay_type_nm for o in options})

        normalized.append(
            NormalizedMortgageLoan(
                fin_co_no=base.fin_co_no,
                fin_prdt_cd=base.fin_prdt_cd,
                bank_name=base.kor_co_nm,
                product_name=base.fin_prdt_nm,
                join_way=base.join_way,
                loan_limit=base.loan_lmt,
                early_repay_fee=base.erly_rpay_fee,
                min_rate=min(min_rates) if min_rates else None,
                max_rate=max(max_rates) if max_rates else None,
                avg_rate=(sum(avg_rates) / len(avg_rates)) if avg_rates else None,
                repay_types=repay_types,
            )
        )
    return normalized


def normalize_mortgage_loan_detail(
    response: MortgageLoanSearchResponse, fin_co_no: str, fin_prdt_cd: str
) -> NormalizedMortgageLoanDetail | None:
    result = response.result
    base = next(
        (b for b in result.baseList if b.fin_co_no == fin_co_no and b.fin_prdt_cd == fin_prdt_cd), None
    )
    if base is None:
        return None

    options = [o for o in result.optionList if o.fin_co_no == fin_co_no and o.fin_prdt_cd == fin_prdt_cd]
    min_rates = [o.lend_rate_min for o in options]
    max_rates = [o.lend_rate_max for o in options]
    avg_rates = [o.lend_rate_avg for o in options if o.lend_rate_avg is not None]

    return NormalizedMortgageLoanDetail(
        fin_co_no=base.fin_co_no,
        fin_prdt_cd=base.fin_prdt_cd,
        bank_name=base.kor_co_nm,
        product_name=base.fin_prdt_nm,
        join_way=base.join_way,
        loan_limit=base.loan_lmt,
        early_repay_fee=base.erly_rpay_fee,
        min_rate=min(min_rates) if min_rates else None,
        max_rate=max(max_rates) if max_rates else None,
        avg_rate=(sum(avg_rates) / len(avg_rates)) if avg_rates else None,
        repay_types=sorted({o.rpay_type_nm for o in options}),
        loan_inci_expn=base.loan_inci_expn,
        dly_rate=base.dly_rate,
        rate_options=[
            LoanRateOption(
                repay_type_nm=o.rpay_type_nm,
                lend_rate_type_nm=o.lend_rate_type_nm,
                lend_rate_min=o.lend_rate_min,
                lend_rate_max=o.lend_rate_max,
                lend_rate_avg=o.lend_rate_avg,
            )
            for o in options
        ],
    )


def normalize_rent_house_loans(response: RentHouseLoanSearchResponse) -> list[NormalizedRentHouseLoan]:
    result = response.result
    options_by_product = _group_by(result.optionList, _product_key)

    normalized = []
    for base in result.baseList:
        options = options_by_product.get(_product_key(base), [])
        min_rates = [o.lend_rate_min for o in options]
        max_rates = [o.lend_rate_max for o in options]
        avg_rates = [o.lend_rate_avg for o in options if o.lend_rate_avg is not None]
        repay_types = sorted({o.rpay_type_nm for o in options})

        normalized.append(
            NormalizedRentHouseLoan(
                fin_co_no=base.fin_co_no,
                fin_prdt_cd=base.fin_prdt_cd,
                bank_name=base.kor_co_nm,
                product_name=base.fin_prdt_nm,
                join_way=base.join_way,
                loan_limit=base.loan_lmt,
                early_repay_fee=base.erly_rpay_fee,
                min_rate=min(min_rates) if min_rates else None,
                max_rate=max(max_rates) if max_rates else None,
                avg_rate=(sum(avg_rates) / len(avg_rates)) if avg_rates else None,
                repay_types=repay_types,
            )
        )
    return normalized


def normalize_rent_house_loan_detail(
    response: RentHouseLoanSearchResponse, fin_co_no: str, fin_prdt_cd: str
) -> NormalizedRentHouseLoanDetail | None:
    result = response.result
    base = next(
        (b for b in result.baseList if b.fin_co_no == fin_co_no and b.fin_prdt_cd == fin_prdt_cd), None
    )
    if base is None:
        return None

    options = [o for o in result.optionList if o.fin_co_no == fin_co_no and o.fin_prdt_cd == fin_prdt_cd]
    min_rates = [o.lend_rate_min for o in options]
    max_rates = [o.lend_rate_max for o in options]
    avg_rates = [o.lend_rate_avg for o in options if o.lend_rate_avg is not None]

    return NormalizedRentHouseLoanDetail(
        fin_co_no=base.fin_co_no,
        fin_prdt_cd=base.fin_prdt_cd,
        bank_name=base.kor_co_nm,
        product_name=base.fin_prdt_nm,
        join_way=base.join_way,
        loan_limit=base.loan_lmt,
        early_repay_fee=base.erly_rpay_fee,
        min_rate=min(min_rates) if min_rates else None,
        max_rate=max(max_rates) if max_rates else None,
        avg_rate=(sum(avg_rates) / len(avg_rates)) if avg_rates else None,
        repay_types=sorted({o.rpay_type_nm for o in options}),
        loan_inci_expn=base.loan_inci_expn,
        dly_rate=base.dly_rate,
        rate_options=[
            LoanRateOption(
                repay_type_nm=o.rpay_type_nm,
                lend_rate_type_nm=o.lend_rate_type_nm,
                lend_rate_min=o.lend_rate_min,
                lend_rate_max=o.lend_rate_max,
                lend_rate_avg=o.lend_rate_avg,
            )
            for o in options
        ],
    )


def normalize_credit_loans(response: CreditLoanSearchResponse) -> list[NormalizedCreditLoan]:
    result = response.result
    options_by_product = _group_by(result.optionList, _product_key)

    normalized = []
    for base in result.baseList:
        options = options_by_product.get(_product_key(base), [])
        grade_rates = [
            getattr(o, field)
            for o in options
            for field in CREDIT_GRADE_FIELDS
            if getattr(o, field) is not None
        ]
        avg_rates = [o.crdt_grad_avg for o in options if o.crdt_grad_avg is not None]

        normalized.append(
            NormalizedCreditLoan(
                fin_co_no=base.fin_co_no,
                fin_prdt_cd=base.fin_prdt_cd,
                bank_name=base.kor_co_nm,
                product_name=base.fin_prdt_nm,
                join_way=base.join_way,
                cb_name=base.cb_name,
                best_grade_rate=min(grade_rates) if grade_rates else None,
                worst_grade_rate=max(grade_rates) if grade_rates else None,
                avg_rate=(sum(avg_rates) / len(avg_rates)) if avg_rates else None,
            )
        )
    return normalized


def normalize_credit_loan_detail(
    response: CreditLoanSearchResponse, fin_co_no: str, fin_prdt_cd: str
) -> NormalizedCreditLoanDetail | None:
    result = response.result
    base = next(
        (b for b in result.baseList if b.fin_co_no == fin_co_no and b.fin_prdt_cd == fin_prdt_cd), None
    )
    if base is None:
        return None

    options = [o for o in result.optionList if o.fin_co_no == fin_co_no and o.fin_prdt_cd == fin_prdt_cd]
    grade_rates = [
        CreditGradeRate(field=field, rate=getattr(o, field))
        for o in options
        for field in CREDIT_GRADE_FIELDS
        if getattr(o, field) is not None
    ]
    flat_rates = [gr.rate for gr in grade_rates]
    avg_rates = [o.crdt_grad_avg for o in options if o.crdt_grad_avg is not None]

    return NormalizedCreditLoanDetail(
        fin_co_no=base.fin_co_no,
        fin_prdt_cd=base.fin_prdt_cd,
        bank_name=base.kor_co_nm,
        product_name=base.fin_prdt_nm,
        join_way=base.join_way,
        cb_name=base.cb_name,
        best_grade_rate=min(flat_rates) if flat_rates else None,
        worst_grade_rate=max(flat_rates) if flat_rates else None,
        avg_rate=(sum(avg_rates) / len(avg_rates)) if avg_rates else None,
        crdt_lend_rate_type_nm=options[0].crdt_lend_rate_type_nm if options else "",
        grade_rates=grade_rates,
    )


def normalize_business_loans(response: BusinessLoanSearchResponse) -> list[NormalizedBusinessLoan]:
    """val1/2/3_grade_* 필드는 FSS 문서상 기준이 불명확해 제외하고, lend_rate_min/max/avg만 사용한다."""
    result = response.result
    options_by_product = _group_by(result.optionList, _product_key)

    normalized = []
    for base in result.baseList:
        options = options_by_product.get(_product_key(base), [])
        min_rates = [o.lend_rate_min for o in options]
        max_rates = [o.lend_rate_max for o in options]
        avg_rates = [o.lend_rate_avg for o in options if o.lend_rate_avg is not None]

        normalized.append(
            NormalizedBusinessLoan(
                fin_co_no=base.fin_co_no,
                fin_prdt_cd=base.fin_prdt_cd,
                bank_name=base.kor_co_nm,
                product_name=base.fin_prdt_nm,
                join_way=base.join_way,
                use_way=base.use_way,
                loan_limit=base.loan_limit,
                min_rate=min(min_rates) if min_rates else None,
                max_rate=max(max_rates) if max_rates else None,
                avg_rate=(sum(avg_rates) / len(avg_rates)) if avg_rates else None,
            )
        )
    return normalized


def normalize_business_loan_detail(
    response: BusinessLoanSearchResponse, fin_co_no: str, fin_prdt_cd: str
) -> NormalizedBusinessLoanDetail | None:
    result = response.result
    base = next(
        (b for b in result.baseList if b.fin_co_no == fin_co_no and b.fin_prdt_cd == fin_prdt_cd), None
    )
    if base is None:
        return None

    options = [o for o in result.optionList if o.fin_co_no == fin_co_no and o.fin_prdt_cd == fin_prdt_cd]
    min_rates = [o.lend_rate_min for o in options]
    max_rates = [o.lend_rate_max for o in options]
    avg_rates = [o.lend_rate_avg for o in options if o.lend_rate_avg is not None]

    return NormalizedBusinessLoanDetail(
        fin_co_no=base.fin_co_no,
        fin_prdt_cd=base.fin_prdt_cd,
        bank_name=base.kor_co_nm,
        product_name=base.fin_prdt_nm,
        join_way=base.join_way,
        use_way=base.use_way,
        loan_limit=base.loan_limit,
        min_rate=min(min_rates) if min_rates else None,
        max_rate=max(max_rates) if max_rates else None,
        avg_rate=(sum(avg_rates) / len(avg_rates)) if avg_rates else None,
        fin_prdt_type_nm=base.fin_prdt_type_nm,
        loan_type=base.loan_type,
        loan_limit_detl=base.loan_limit_detl,
        join_deny_detl=base.join_deny_detl,
        loan_term=base.loan_term,
        early_repay_fee=base.erly_rpay_fee,
        loan_inci_expn=base.loan_inci_expn,
        dly_rate=base.dly_rate,
    )


def normalize_companies(response: CompanySearchResponse) -> list[NormalizedCompany]:
    result = response.result
    areas_by_company = _group_by(result.optionList, lambda o: (o.fin_co_no,))

    normalized = []
    for base in result.baseList:
        areas = areas_by_company.get((base.fin_co_no,), [])
        area_names = sorted({a.area_nm for a in areas if a.exis_yn == "Y"})

        normalized.append(
            NormalizedCompany(
                fin_co_no=base.fin_co_no,
                bank_name=base.kor_co_nm,
                homepage_url=base.homp_url,
                call_center=base.cal_tel,
                areas=area_names,
            )
        )
    return normalized
