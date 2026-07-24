"""마이데이터 표준 API 클라이언트의 목업.

실제 마이데이터 API는 인가 제약으로 연동할 수 없어, 동일한 스펙을 따르는
mock 데이터를 반환하는 클라이언트로 대체한다. FSSClient와 동일한 인터페이스
형태(컨텍스트 매니저 등)를 유지해, 추후 실제 마이데이터 API로 교체할 때
내부 구현만 바꾸면 되도록 한다.

인가(토큰 발급/검증)는 app/clients/mydata_auth_client.py가 담당한다.
"""

from __future__ import annotations

from app.schemas import UserProfile
from app.services.store import get_user_profile as _load_user_profile


class MyDataError(Exception):
    """MyData 클라이언트 오류."""


class MyDataClient:
    def __init__(self) -> None:
        pass

    def __enter__(self) -> "MyDataClient":
        return self

    def __exit__(self, *exc_info: object) -> None:
        pass

    def get_user_profile(self, user_id: str) -> UserProfile:
        """user_id의 마이데이터 기반 유저 프로필을 반환한다 (목업: 로컬 mock 데이터)."""
        profile = _load_user_profile(user_id)
        if profile is None:
            raise MyDataError(f"등록되지 않은 user_id: {user_id!r}")
        return profile
