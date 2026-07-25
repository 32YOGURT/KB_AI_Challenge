"""카드-008: 국내 승인내역 조회."""

from pydantic import BaseModel


class CardApprovalItem(BaseModel):
    approved_num: str
    approved_dtime: str
    status: str
    pay_type: str
    trans_dtime: str | None = None
    merchant_name: str
    merchant_regno: str | None = None
    approved_amt: int
    modified_amt: int | None = None
    total_install_cnt: int | None = None


class CardApprovalResponse(BaseModel):
    rsp_code: str
    rsp_msg: str
    next_page: str | None = None
    approved_cnt: int
    approved_list: list[CardApprovalItem] = []
