"""은행-001: 계좌 목록 조회."""

from pydantic import BaseModel


class AccountItem(BaseModel):
    account_num: str
    is_consent: bool
    seqno: str
    is_foreign_deposit: bool
    prod_name: str
    is_minus: bool
    account_type: str
    account_status: str


class AccountListResponse(BaseModel):
    rsp_code: str
    rsp_msg: str
    search_timestamp: str
    reg_date: str
    next_page: str | None = None
    account_cnt: int
    account_list: list[AccountItem] = []
