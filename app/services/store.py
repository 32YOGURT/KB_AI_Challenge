import json
from functools import lru_cache
from pathlib import Path

from app.schemas import UserSummary

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@lru_cache
def load_mydata_mock() -> dict:
    """마이데이터 mock 데이터.

    구조: user_id -> {
        "display_name": str,
        "institutions": {org_code: {섹션명: [원본 dict, ...]}},  # 계좌 관련(기관별 조회)
        섹션명: [원본 dict, ...],                                  # 카드 관련(기관 무관)
    }
    """
    return json.loads((DATA_DIR / "mydata_mock.json").read_text(encoding="utf-8"))


def mydata_user_exists(user_id: str) -> bool:
    return user_id in load_mydata_mock()


def list_mydata_users() -> list[UserSummary]:
    return [
        UserSummary(
            id=user_id,
            display_name=data.get("display_name", user_id),
            description=data.get("description", ""),
        )
        for user_id, data in load_mydata_mock().items()
    ]


def get_mydata_section(user_id: str, section: str) -> list[dict]:
    return load_mydata_mock().get(user_id, {}).get(section, [])


def list_mydata_institutions(user_id: str) -> list[str]:
    """user_id가 마이데이터 전송요구(동의)한 금융회사(org_code) 목록."""
    return list(load_mydata_mock().get(user_id, {}).get("institutions", {}).keys())


def get_mydata_institution_section(user_id: str, org_code: str, section: str) -> list[dict]:
    institutions = load_mydata_mock().get(user_id, {}).get("institutions", {})
    return institutions.get(org_code, {}).get(section, [])
