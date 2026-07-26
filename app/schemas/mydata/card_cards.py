"""카드-001: 카드 목록 조회."""

from pydantic import BaseModel


class CardItem(BaseModel):
    card_id: str
    card_num: str
    is_consent: bool
    card_name: str
    card_member: str
    card_type: str


class CardListResponse(BaseModel):
    rsp_code: str
    rsp_msg: str
    search_timestamp: str
    next_page: str | None = None
    card_cnt: int
    card_list: list[CardItem] = []
