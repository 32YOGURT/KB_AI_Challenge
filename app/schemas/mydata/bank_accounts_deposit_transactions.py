"""은행-004: 수신계좌 거래내역 조회."""

from pydantic import BaseModel


class AccountTransactionItem(BaseModel):
    trans_dtime: str
    trans_no: str
    trans_type: str
    trans_class: str
    currency_code: str
    trans_amt: float
    balance_amt: float
    paid_in_cnt: int
    trans_memo: str | None = None


class AccountTransactionResponse(BaseModel):
    rsp_code: str
    rsp_msg: str
    next_page: str | None = None
    trans_cnt: int
    trans_list: list[AccountTransactionItem] = []
