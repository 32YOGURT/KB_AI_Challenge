from pydantic import BaseModel


class UserSummary(BaseModel):
    """유저 식별/표시용 최소 정보 (프론트 유저 전환 목록 등). 금융 데이터는 담지 않는다 —
    금융 데이터는 app/schemas/signals/*(마이데이터 신호)에서 가져온다."""

    id: str
    display_name: str
