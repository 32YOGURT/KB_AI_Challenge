from fastapi import APIRouter, Query

from app.schemas.catalog import CatalogProduct
from app.services.catalog import list_catalog_products

router = APIRouter(prefix="/api", tags=["catalog"])


@router.get("/catalog/products", response_model=list[CatalogProduct])
def get_catalog_products(category: str | None = Query(None)) -> list[CatalogProduct]:
    return list_catalog_products(category)
