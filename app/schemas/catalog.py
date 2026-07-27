from pydantic import BaseModel


class CatalogProduct(BaseModel):
    """크롤링 파이프라인이 만드는 상품 카탈로그 한 건 (product_id로 그룹핑된 대표 문서 기준)."""

    product_id: str
    bank: str
    name: str
    category: str
    source_url: str
