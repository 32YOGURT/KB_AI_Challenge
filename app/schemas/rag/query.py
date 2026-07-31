from pydantic import BaseModel


class SearchQuery(BaseModel):
    """검색 쿼리 하나. doc_types를 지정하면 그 문서 종류에서만 검색한다(None이면 제한 없음)."""

    text: str
    doc_types: list[str] | None = None
