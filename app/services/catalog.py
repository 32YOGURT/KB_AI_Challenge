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


@lru_cache
def load_catalog() -> dict[str, CatalogProduct]:
    catalog: dict[str, CatalogProduct] = {}
    for doc in _load_manifest():
        product_id = doc.get("product_id")
        if not product_id or product_id in catalog:
            continue
        catalog[product_id] = CatalogProduct(
            product_id=product_id,
            bank=doc["company"],
            name=doc["product_name"],
            category=doc["category"],
            source_url=doc["source_page_url"],
        )
    return catalog


def list_catalog_products(category: str | None = None) -> list[CatalogProduct]:
    products = list(load_catalog().values())
    if category:
        products = [p for p in products if p.category == category]
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
