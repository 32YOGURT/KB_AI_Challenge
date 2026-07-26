from typing import Literal

from pydantic import BaseModel

DocType = Literal["상품설명서", "특약", "기본약관", "약정서"]


class ClauseChunk(BaseModel):
    """Qdrant `product_clauses` 컬렉션의 payload 스키마. 조항(제N조) 단위로 청킹됨."""

    product_id: str | None = None  # None이면 특정 상품이 아니라 company 공통 문서(기본약관 등)
    company: str
    category: str
    doc_type: DocType
    clause_title: str
    text: str
    source: str
    source_file: str
    page: int | None = None
    effective_date: str | None = None
    content_hash: str
    has_table: bool = False


class ClauseSearchResult(ClauseChunk):
    score: float
