"""RAG 검색 쿼리를 결정적으로(LLM 호출 없이) 생성한다. 카테고리별 위험 키워드 템플릿 +
상품명 조합. LLM 기반 쿼리 생성(유저별 맞춤)은 상품/데이터가 늘어난 뒤 비교해서 결정하기로
보류한 상태 — 지금은 이 정도로 검색 품질이 충분한지부터 검증한다."""

from app.schemas import Product

_CATEGORY_QUERY_TEMPLATES = {
    "예금": "중도해지 이율 만기 유의사항 수수료",
    "적금": "우대금리 조건 중도해지 이율 만기 유의사항",
    "대출": "중도상환수수료 변동금리 연체이자 상환조건 유의사항",
    "카드": "연회비 부가서비스 조건 유의사항",
}
_DEFAULT_TEMPLATE = "유의사항 조건 수수료"


def build_search_query(product: Product) -> str:
    template = _CATEGORY_QUERY_TEMPLATES.get(product.category, _DEFAULT_TEMPLATE)
    return f"{product.name} {template}"
