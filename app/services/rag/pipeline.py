import re

from app.schemas import CheckResponse, ClauseSearchResult, RiskBasis, RiskPoint
from app.schemas.check import CheckSubject
from app.services.mydata.user_signals import get_user_signals
from app.services.rag.llm_inference import infer_risk_report
from app.services.rag.query_builder import build_search_queries
from app.services.rag.retrieval import search_clauses_multi

_WHITESPACE_RE = re.compile(r"\s+")


def _verify_quote(quote: str | None, chunk_text: str) -> str | None:
    """LLM이 낸 evidence_quote가 실제로 조항 원문에 있는지 확인한다 (공백 차이는 무시).

    LLM이 의역하거나 지어낸 인용은 프론트에서 하이라이팅 대상 문자열을 페이지에서
    찾지 못해 조용히 실패할 뿐 아니라, 근거 없는 인용을 그대로 보여주는 셈이 된다 —
    여기서 걸러 None으로 버리면 프론트는 하이라이팅만 생략하고 나머지(페이지/출처)는
    그대로 보여준다.
    """
    if not quote:
        return None
    normalized_quote = _WHITESPACE_RE.sub("", quote)
    normalized_text = _WHITESPACE_RE.sub("", chunk_text)
    return quote if normalized_quote in normalized_text else None


def _build_basis(
    clause_index: int | None, quote: str | None, clauses: list[ClauseSearchResult]
) -> RiskBasis | None:
    """LLM이 고른 번호(1-based)로 실제 조항을 찾아 근거를 조립한다.

    조항 텍스트를 LLM이 직접 쓰게 하면 원문 PDF/페이지를 역추적할 수 없어서, 번호만
    받아 여기서 결정론적으로 채운다. 범위를 벗어난 번호는 근거 없음으로 처리한다.
    """
    if clause_index is None or not 1 <= clause_index <= len(clauses):
        return None
    chunk = clauses[clause_index - 1]
    return RiskBasis(
        clause=chunk.clause_title,
        source=chunk.source,
        source_key=chunk.source_key,
        page=chunk.page,
        quote=_verify_quote(quote, chunk.text),
    )


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
        points=[
            RiskPoint(text=p["text"], basis=_build_basis(p["clause_index"], p["evidence_quote"], clauses))
            for p in result["points"]
        ],
    )
