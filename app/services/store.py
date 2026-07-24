import json
from functools import lru_cache
from pathlib import Path

from app.models import Product, UserProfile

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@lru_cache
def load_products() -> dict[str, Product]:
    raw = json.loads((DATA_DIR / "products.json").read_text(encoding="utf-8"))
    return {p["id"]: Product(**p) for p in raw}


@lru_cache
def load_user_profiles() -> dict[str, UserProfile]:
    raw = json.loads((DATA_DIR / "user_profiles.json").read_text(encoding="utf-8"))
    return {u["id"]: UserProfile(**u) for u in raw}


def get_product(product_id: str) -> Product | None:
    return load_products().get(product_id)


def get_user_profile(user_id: str) -> UserProfile | None:
    return load_user_profiles().get(user_id)


def list_products() -> list[Product]:
    return list(load_products().values())
