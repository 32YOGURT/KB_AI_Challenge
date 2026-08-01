"""크롤러가 만드는 crawled_data/manifest.json(문서 단위 메타데이터 배열)을 상품 단위
카탈로그로 정제한다. product_id가 없는 문서(공통 약관 등)는 상품이 아니므로 제외하고,
같은 product_id를 공유하는 문서들은 대표 1건으로 묶는다.
"""

import json
from functools import lru_cache
from pathlib import Path

from app.schemas.catalog import CatalogProduct
from app.schemas.check import CheckSubject

MANIFEST_PATH = Path(__file__).resolve().parent.parent.parent / "crawled_data" / "manifest.json"


@lru_cache
def _load_manifest() -> list[dict]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _representative(docs: list[dict]) -> dict:
    """상품을 대표할 문서. 소비자용 요약인 상품설명서를 우선한다 — manifest 순서(크롤링 순서)에
    기대면 같은 상품이 문서에 따라 다른 category로 분류돼 검색 축까지 달라진다."""
    return next((d for d in docs if d.get("doc_type") == "상품설명서"), docs[0])


@lru_cache
def load_catalog() -> dict[str, CatalogProduct]:
    grouped: dict[str, list[dict]] = {}
    for doc in _load_manifest():
        if doc.get("product_id") and doc.get("product_type"):
            grouped.setdefault(doc["product_id"], []).append(doc)

    catalog: dict[str, CatalogProduct] = {}
    for product_id, docs in grouped.items():
        rep = _representative(docs)
        catalog[product_id] = CatalogProduct(
            product_id=product_id,
            bank=rep["company"],
            name=rep["product_name"],
            product_type=rep["product_type"],
            category=rep["category"],
            sub_category=rep["sub_category"],
            doc_key=rep["saved_path"],
        )
    return catalog


def list_catalog_products(product_type: str | None = None) -> list[CatalogProduct]:
    products = list(load_catalog().values())
    if product_type:
        products = [p for p in products if p.product_type == product_type]
    return products


def get_catalog_product(product_id: str) -> CatalogProduct | None:
    return load_catalog().get(product_id)


def get_check_subject(product_id: str) -> CheckSubject | None:
    product = get_catalog_product(product_id)
    if product is None:
        return None
    return CheckSubject(
        product_id=product.product_id,
        bank=product.bank,
        name=product.name,
        category=product.category,
    )
