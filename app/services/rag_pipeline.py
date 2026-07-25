from app.schemas import CheckResponse, Product, RiskBasis, UserProfile
from app.services.llm_inference import infer_risk_report
from app.services.query_builder import build_search_query
from app.services.rag import search_clauses


def generate_risk_report(product: Product, user: UserProfile) -> CheckResponse:
    """RAG 검색으로 약관 조항을 핀포인트 추출한 뒤, 유저 데이터와 결합해 LLM 추론을 요청한다."""
    query = build_search_query(product)
    clauses = search_clauses(product_id=product.id, company=product.bank, query=query)
    result = infer_risk_report(product, user, clauses)

    return CheckResponse(
        product_id=product.id,
        product_name=product.name,
        user_id=user.id,
        risk_level=result["risk_level"],
        headline=result["headline"],
        summary_lines=result["summary_lines"],
        basis=[RiskBasis(clause=b["clause"], source=b["source"]) for b in result["basis"]],
    )
