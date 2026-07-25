"""은행-003: 수신계좌 추가정보 조회."""

from pydantic import BaseModel


class AccountDetailItem(BaseModel):
    currency_code: str
    balance_amt: float
    withdrawable_amt: float
    offered_rate: float
    last_paid_in_cnt: int


class AccountDetailResponse(BaseModel):
    rsp_code: str
    rsp_msg: str
    search_timestamp: str
    detail_cnt: int
    detail_list: list[AccountDetailItem] = []
