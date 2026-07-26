"""마이데이터 인가(OAuth) 목업.

실제 마이데이터 연동에는 OAuth 인가 서버가 필요하지만, 인가 제약상 데모에서는
붙일 수 없어 토큰에 user_id를 그대로 인코딩하는 stateless 목업으로 대체한다.
서명/만료 검증은 하지 않는다 — 서버가 재시작돼도(--reload) 발급된 토큰이
계속 유효하도록 하기 위한 선택.
"""

from __future__ import annotations

_TOKEN_PREFIX = "mock."


class MyDataAuthError(Exception):
    """MyData 인가 오류."""


def issue_token(user_id: str) -> str:
    """user_id를 인코딩한 목업 토큰을 발급한다."""
    return f"{_TOKEN_PREFIX}{user_id}"


def resolve_user_id(token: str) -> str:
    """토큰에서 user_id를 복원한다."""
    if not token.startswith(_TOKEN_PREFIX):
        raise MyDataAuthError(f"유효하지 않은 토큰: {token!r}")
    return token.removeprefix(_TOKEN_PREFIX)
