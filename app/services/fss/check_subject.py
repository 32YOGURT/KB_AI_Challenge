"""FSS 카테고리별 상품을 조회해 RAG/LLM 파이프라인용 CheckSubject로 변환한다.

각 카테고리의 상세 조회는 이미 프론트 상세 페이지용으로 만든 normalize_xxx_detail()을
그대로 재사용한다 — 새 FSS 파싱 로직이 필요 없다.
"""

from app.clients.fss_client import FSSClient
from app.schemas.check import CheckSubject
from app.schemas.fss.normalized import FssProductCategory
from app.services.fss.normalize import (
    normalize_business_loan_detail,
    normalize_credit_loan_detail,
    normalize_deposit_detail,
    normalize_mortgage_loan_detail,
    normalize_rent_house_loan_detail,
    normalize_saving_detail,
)

_CATEGORY_LABELS: dict[FssProductCategory, str] = {
    "deposit": "예금",
    "saving": "적금",
    "mortgage_loan": "대출",
    "rent_house_loan": "대출",
    "credit_loan": "대출",
    "business_loan": "대출",
}


def _rate_summary(min_rate: float | None, max_rate: float | None) -> str:
    if min_rate is None and max_rate is None:
        return "금리 정보 없음"
    if min_rate is not None and max_rate is not None and min_rate != max_rate:
        return f"연 {min_rate}~{max_rate}%"
    rate = max_rate if max_rate is not None else min_rate
    return f"연 {rate}%"


def _format_fields(pairs: list[tuple[str, str | None]]) -> str:
    lines = [f"{label}: {value}" for label, value in pairs if value]
    return "\n".join(lines) if lines else "특이사항 없음"


def build_check_subject(category: FssProductCategory, fin_co_no: str, fin_prdt_cd: str) -> CheckSubject | None:
    """FSS API를 조회해 해당 상품의 CheckSubject를 만든다. 상품을 못 찾으면 None."""
    label = _CATEGORY_LABELS[category]

    with FSSClient() as client:
        if category == "deposit":
            detail = normalize_deposit_detail(client.search_deposit_products("020000"), fin_co_no, fin_prdt_cd)
            if detail is None:
                return None
            return CheckSubject(
                category=category,
                fin_co_no=fin_co_no,
                fin_prdt_cd=fin_prdt_cd,
                bank=detail.bank_name,
                name=detail.product_name,
                category_label=label,
                rate_summary=_rate_summary(detail.min_rate, detail.max_rate),
                conditions_text=_format_fields(
                    [
                        ("우대조건", detail.spcl_cnd),
                        ("유의사항", detail.etc_note),
                        ("가입 대상", detail.join_member),
                        ("가입 제한", detail.join_deny),
                        ("만기 후 이자율", detail.mtrt_int),
                    ]
                ),
            )

        if category == "saving":
            detail = normalize_saving_detail(client.search_saving_products("020000"), fin_co_no, fin_prdt_cd)
            if detail is None:
                return None
            return CheckSubject(
                category=category,
                fin_co_no=fin_co_no,
                fin_prdt_cd=fin_prdt_cd,
                bank=detail.bank_name,
                name=detail.product_name,
                category_label=label,
                rate_summary=_rate_summary(detail.min_rate, detail.max_rate),
                conditions_text=_format_fields(
                    [
                        ("우대조건", detail.spcl_cnd),
                        ("유의사항", detail.etc_note),
                        ("가입 대상", detail.join_member),
                        ("가입 제한", detail.join_deny),
                        ("만기 후 이자율", detail.mtrt_int),
                        ("적립유형", ", ".join(detail.reserve_types) or None),
                    ]
                ),
            )

        if category == "mortgage_loan":
            detail = normalize_mortgage_loan_detail(
                client.search_mortgage_loan_products("020000"), fin_co_no, fin_prdt_cd
            )
            if detail is None:
                return None
            return CheckSubject(
                category=category,
                fin_co_no=fin_co_no,
                fin_prdt_cd=fin_prdt_cd,
                bank=detail.bank_name,
                name=detail.product_name,
                category_label=label,
                rate_summary=_rate_summary(detail.min_rate, detail.max_rate),
                conditions_text=_format_fields(
                    [
                        ("대출 한도", detail.loan_limit),
                        ("중도상환수수료", detail.early_repay_fee),
                        ("부대비용", detail.loan_inci_expn),
                        ("연체이자율", detail.dly_rate),
                    ]
                ),
            )

        if category == "rent_house_loan":
            detail = normalize_rent_house_loan_detail(
                client.search_rent_house_loan_products("020000"), fin_co_no, fin_prdt_cd
            )
            if detail is None:
                return None
            return CheckSubject(
                category=category,
                fin_co_no=fin_co_no,
                fin_prdt_cd=fin_prdt_cd,
                bank=detail.bank_name,
                name=detail.product_name,
                category_label=label,
                rate_summary=_rate_summary(detail.min_rate, detail.max_rate),
                conditions_text=_format_fields(
                    [
                        ("대출 한도", detail.loan_limit),
                        ("중도상환수수료", detail.early_repay_fee),
                        ("부대비용", detail.loan_inci_expn),
                        ("연체이자율", detail.dly_rate),
                    ]
                ),
            )

        if category == "credit_loan":
            detail = normalize_credit_loan_detail(client.search_credit_loan_products("020000"), fin_co_no, fin_prdt_cd)
            if detail is None:
                return None
            return CheckSubject(
                category=category,
                fin_co_no=fin_co_no,
                fin_prdt_cd=fin_prdt_cd,
                bank=detail.bank_name,
                name=detail.product_name,
                category_label=label,
                rate_summary=_rate_summary(detail.best_grade_rate, detail.worst_grade_rate),
                conditions_text=_format_fields(
                    [
                        ("취급 CB사", detail.cb_name),
                        ("금리 유형", detail.crdt_lend_rate_type_nm),
                    ]
                ),
            )

        # category == "business_loan"
        detail = normalize_business_loan_detail(
            client.search_business_loan_products("020000"), fin_co_no, fin_prdt_cd
        )
        if detail is None:
            return None
        return CheckSubject(
            category=category,
            fin_co_no=fin_co_no,
            fin_prdt_cd=fin_prdt_cd,
            bank=detail.bank_name,
            name=detail.product_name,
            category_label=label,
            rate_summary=_rate_summary(detail.min_rate, detail.max_rate),
            conditions_text=_format_fields(
                [
                    ("이용 용도", detail.use_way),
                    ("대출 한도", detail.loan_limit),
                    ("대출 한도 상세", detail.loan_limit_detl),
                    ("대출 제한 상세", detail.join_deny_detl),
                    ("대출 기간", detail.loan_term),
                    ("중도상환수수료", detail.early_repay_fee),
                    ("부대비용", detail.loan_inci_expn),
                    ("연체이자율", detail.dly_rate),
                ]
            ),
        )
