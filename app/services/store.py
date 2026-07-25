import json
from functools import lru_cache
from pathlib import Path

from app.schemas import Product, UserProfile

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


@lru_cache
def load_mydata_mock() -> dict:
    """마이데이터 mock 데이터.

    구조: user_id -> {
        "institutions": {org_code: {섹션명: [원본 dict, ...]}},  # 계좌 관련(기관별 조회)
        섹션명: [원본 dict, ...],                                  # 카드 관련(기관 무관)
    }
    """
    return json.loads((DATA_DIR / "mydata_mock.json").read_text(encoding="utf-8"))


def get_mydata_section(user_id: str, section: str) -> list[dict]:
    return load_mydata_mock().get(user_id, {}).get(section, [])


def list_mydata_institutions(user_id: str) -> list[str]:
    """user_id가 마이데이터 전송요구(동의)한 금융회사(org_code) 목록."""
    return list(load_mydata_mock().get(user_id, {}).get("institutions", {}).keys())


def get_mydata_institution_section(user_id: str, org_code: str, section: str) -> list[dict]:
    institutions = load_mydata_mock().get(user_id, {}).get("institutions", {})
    return institutions.get(org_code, {}).get(section, [])
