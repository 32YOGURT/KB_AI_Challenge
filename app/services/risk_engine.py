import operator

from app.models import CheckResponse, Product, ProductCondition, RiskBasis, UserProfile

_OPERATORS = {
    "lt": operator.lt,
    "lte": operator.le,
    "gt": operator.gt,
    "gte": operator.ge,
    "eq": operator.eq,
}

_SEVERITY_ORDER = {"RED": 0, "YELLOW": 1}


def _condition_matches(condition: ProductCondition, user: UserProfile) -> bool:
    value = getattr(user, condition.field, None)
    if value is None:
        return False
    return _OPERATORS[condition.operator](value, condition.threshold)


def generate_risk_report(product: Product, user: UserProfile) -> CheckResponse:
    """Rule-based mock scan. Signature/output stays stable so this can later be
    swapped for the RAG + LLM pipeline described in CLAUDE.md without touching callers."""
    matched = [c for c in product.risk_conditions if _condition_matches(c, user)]
    matched.sort(key=lambda c: _SEVERITY_ORDER[c.severity])

    if not matched:
        return CheckResponse(
            product_id=product.id,
            product_name=product.name,
            user_id=user.id,
            risk_level="GREEN",
            headline="현재 프로필 기준 특이 위험 없음",
            summary_lines=[
                "확인된 우대조건 미달이나 중도해지 페널티 위험이 없습니다.",
                f"{product.bank} {product.name}의 기본 조건이 현재 소비 패턴과 잘 맞습니다.",
                "가입 후에도 조건 변경 시 다시 확인하는 것을 권장합니다.",
            ],
            basis=[],
        )

    top = matched[0]
    return CheckResponse(
        product_id=product.id,
        product_name=product.name,
        user_id=user.id,
        risk_level=top.severity,
        headline=top.headline,
        summary_lines=top.summary_lines,
        basis=[RiskBasis(clause=c.basis_clause, source=c.basis_source) for c in matched],
    )
