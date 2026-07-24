from fastapi import APIRouter, HTTPException

from app.schemas import Product, ProductSummary, UserProfile
from app.services.store import get_product, list_products, load_user_profiles

router = APIRouter(prefix="/api", tags=["products"])


@router.get("/products", response_model=list[ProductSummary])
def get_products() -> list[ProductSummary]:
    return [
        ProductSummary(
            id=p.id,
            name=p.name,
            bank=p.bank,
            category=p.category,
            headline_rate=p.headline_rate,
            description=p.description,
        )
        for p in list_products()
    ]


@router.get("/products/{product_id}", response_model=Product)
def get_product_detail(product_id: str) -> Product:
    product = get_product(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.get("/users", response_model=list[UserProfile])
def get_users() -> list[UserProfile]:
    return list(load_user_profiles().values())
