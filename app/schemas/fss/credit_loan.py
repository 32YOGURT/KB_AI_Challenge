from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel


class BaseListItem(BaseModel):
    dcls_month: str
    fin_co_no: str
    fin_prdt_cd: str
    crdt_prdt_type: str
    kor_co_nm: str
    fin_prdt_nm: str
    join_way: str
    cb_name: str
    crdt_prdt_type_nm: str
    dcls_strt_day: str
    dcls_end_day: Any
    fin_co_subm_day: str


class OptionListItem(BaseModel):
    dcls_month: str
    fin_co_no: str
    fin_prdt_cd: str
    crdt_prdt_type: str
    crdt_lend_rate_type: str
    crdt_lend_rate_type_nm: str
    crdt_grad_1: float
    crdt_grad_4: float
    crdt_grad_5: float
    crdt_grad_6: float
    crdt_grad_10: Optional[float]
    crdt_grad_11: Optional[float]
    crdt_grad_12: Optional[float]
    crdt_grad_13: Optional[float]
    crdt_grad_avg: float


class Result(BaseModel):
    prdt_div: str
    total_count: str
    max_page_no: str
    now_page_no: str
    err_cd: str
    err_msg: str
    baseList: List[BaseListItem]
    optionList: List[OptionListItem]


class Model(BaseModel):
    result: Result
