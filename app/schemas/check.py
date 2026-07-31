from pydantic import BaseModel


class CheckRequest(BaseModel):
    product_id: str
    user_id: str


class CheckSubject(BaseModel):
    """카탈로그 상품을 RAG 검색/LLM 추론 파이프라인이 쓸 수 있게 평탄화한 뷰.

    product_id/bank/category는 크롤러가 Qdrant ClauseChunk에 저장하는 값과 동일해야
    검색 필터가 맞물린다 (app/services/catalog.py 참고).
    """

    product_id: str
    bank: str
    name: str
    category: str  # "예금"/"적금"/"대출" 등 — query_builder 템플릿 키로도 쓰임


class RiskBasis(BaseModel):
    clause: str
    source: str
    source_key: str  # 원문 PDF(MinIO object key). 재색인 전 조항은 빈 문자열
    page: int | None = None
    quote: str | None = None  # 근거 원문 인용(검증 통과분만). 없으면 프론트가 하이라이팅을 생략


class RiskPoint(BaseModel):
    text: str
    detail: str
    basis: RiskBasis | None = None


class CheckResponse(BaseModel):
    product_id: str
    product_name: str
    user_id: str
    points: list[RiskPoint]
