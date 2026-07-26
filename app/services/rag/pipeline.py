from app.schemas import CheckResponse, Product, RiskBasis
from app.services.mydata.user_signals import get_user_signals
from app.services.rag.llm_inference import infer_risk_report
from app.services.rag.query_builder import build_search_query
from app.services.rag.retrieval import search_clauses


def generate_risk_report(product: Product, user_id: str) -> CheckResponse:
    """RAG 검색으로 약관 조항을 핀포인트 추출하고, 마이데이터 신호와 결합해 LLM 추론을 요청한다."""
    query = build_search_query(product)
    clauses = search_clauses(product_id=product.id, company=product.bank, query=query)
    signals = get_user_signals(user_id)
    result = infer_risk_report(product, signals, clauses)

    return CheckResponse(
        product_id=product.id,
        product_name=product.name,
        user_id=user_id,
        risk_level=result["risk_level"],
        headline=result["headline"],
        summary_lines=result["summary_lines"],
        basis=[RiskBasis(clause=b["clause"], source=b["source"]) for b in result["basis"]],
    )
