from pydantic import BaseModel


class CatalogProduct(BaseModel):
    """크롤링 파이프라인이 만드는 상품 카탈로그 한 건 (product_id로 그룹핑된 대표 문서 기준)."""

    product_id: str
    bank: str
    name: str
    product_type: str  # 은행 무관 정규 분류 (정기예금/적금/입출금자유예금/외화예금/주택청약)
    category: str  # 은행 사이트 원문 분류 — RAG 검색 축(query_builder) 선택 키로 쓰인다
    sub_category: str
    doc_key: str | None = None  # 원문 PDF(상품설명서 우선) object key
