"""은행-002: 수신계좌 기본정보 조회."""

from pydantic import BaseModel


class AccountBasicItem(BaseModel):
    currency_code: str
    saving_method: str
    issue_date: str
    exp_date: str
    commit_amt: float
    monthly_paid_in_amt: float


class AccountBasicResponse(BaseModel):
    rsp_code: str
    rsp_msg: str
    search_timestamp: str
    basic_cnt: int
    basic_list: list[AccountBasicItem] = []
