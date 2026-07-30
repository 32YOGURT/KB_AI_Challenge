"""RAG 검색 쿼리를 결정적으로(LLM 호출 없이) 생성한다. 카테고리마다 위험 축(우대조건/
중도해지/만기/예금자보호 등) 여러 개로 나눠 쿼리를 만든다 — 축을 한 문자열에 뭉치면
top_k 예산 안에서 명시 안 한 축이 밀려나는 문제가 실측으로 확인돼서, 축별로 개별 검색
후 병합하는 쪽(app.services.rag.retrieval.search_clauses_multi)으로 바꿨다.

쿼리 텍스트에 상품명은 넣지 않는다 — 검색이 이미 product_id/company 필터로 후보를
좁히므로 상품명을 쿼리에도 넣으면 변별력 없이 노이즈만 늘어난다 (실측: 상품명을 넣으면
상품설명서 표지처럼 상품명이 반복 등장하는 청크가 조항보다 높은 점수를 받았음).

LLM 기반 쿼리 생성(유저별 맞춤)은 검토 후 보류. 검색 앞단에 LLM 호출을 추가하면 지연이
늘어 이 프로젝트의 핵심 기술 피치("RAG로 0.5초에 검색")와 상충하고, 비결정적이라
재현성도 떨어진다."""

from app.schemas.check import CheckSubject

_CATEGORY_AXIS_TEMPLATES: dict[str, list[str]] = {
    "예금": [
        "중도해지 중도해지이율 중도해지수수료",
        "만기 만기해지 만기후이율",
        "예금자보호 보호한도",
        "유의사항 제한사항 수수료",
    ],
    "적금": [
        "우대금리 우대이율 조건 미달",
        "중도해지 중도해지이율 특별중도해지",
        "만기 만기해지 만기후이율",
        "예금자보호 보호한도",
    ],
    "대출": [
        "중도상환수수료 조기상환",
        "변동금리 금리인상 연체이자",
        "상환조건 유의사항",
    ],
    "카드": [
        "연회비 갱신",
        "부가서비스 조건 실적",
        "유의사항 해지",
    ],
}
_DEFAULT_AXES = ["유의사항 조건 수수료"]


def build_search_queries(subject: CheckSubject) -> list[str]:
    return _CATEGORY_AXIS_TEMPLATES.get(subject.category, _DEFAULT_AXES)
