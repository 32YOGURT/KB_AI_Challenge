from typing import Literal

from pydantic import BaseModel

QueryTier = Literal["general", "description", "user_specific"]


class SearchQuery(BaseModel):
    """검색 쿼리 하나. doc_types를 지정하면 그 문서 종류에서만 검색한다(None이면 제한 없음).

    tier는 이 쿼리가 3계층 중 어디 소속인지, reason은 user_specific 쿼리가 왜 생성됐는지
    (유저 신호의 실제 수치)를 담는다 — 검색된 조항을 LLM에 보여줄 때 그대로 라벨로 붙여서,
    "이 조항이 왜 이 유저와 관련있는지"를 LLM이 추론하지 않고 그대로 전달받게 한다.
    """

    text: str
    doc_types: list[str] | None = None
    tier: QueryTier = "general"
    reason: str | None = None
