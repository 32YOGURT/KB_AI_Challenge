from app.schemas import CheckResponse, RiskBasis, RiskPoint
from app.schemas.check import CheckSubject
from app.services.mydata.user_signals import get_user_signals
from app.services.rag.llm_inference import infer_risk_report
from app.services.rag.query_builder import build_search_queries
from app.services.rag.retrieval import search_clauses_multi


def generate_risk_report(subject: CheckSubject, user_id: str) -> CheckResponse:
    """RAG 검색으로 약관 조항을 핀포인트 추출하고, 마이데이터 신호와 결합해 LLM 추론을 요청한다.

    유저 신호를 검색 쿼리 생성보다 먼저 조회한다 — build_search_queries가 유저 신호를 보고
    검색 축 자체를 개인화하므로(유동성 부족 -> 중도해지 축 강화 등), 검색 이전에 신호가
    필요하다.
    """
    signals = get_user_signals(user_id)
    queries = build_search_queries(subject, signals)
    clauses = search_clauses_multi(product_id=subject.product_id, company=subject.bank, queries=queries)
    result = infer_risk_report(subject, signals, clauses)

    return CheckResponse(
        product_id=subject.product_id,
        product_name=subject.name,
        user_id=user_id,
        risk_level=result["risk_level"],
        points=[
            RiskPoint(
                text=p["text"],
                basis=RiskBasis(clause=p["basis"]["clause"], source=p["basis"]["source"]) if p["basis"] else None,
            )
            for p in result["points"]
        ],
    )
