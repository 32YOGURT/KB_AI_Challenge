from __future__ import annotations

from typing import Any, List

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
    crdt_grad_1: float | None = None
    crdt_grad_4: float | None = None
    crdt_grad_5: float | None = None
    crdt_grad_6: float | None = None
    crdt_grad_10: float | None = None
    crdt_grad_11: float | None = None
    crdt_grad_12: float | None = None
    crdt_grad_13: float | None = None
    crdt_grad_avg: float | None = None


class Result(BaseModel):
    prdt_div: str | None = None
    total_count: int
    max_page_no: int | None = None
    now_page_no: int | None = None
    err_cd: str
    err_msg: str
    baseList: List[BaseListItem] = []
    optionList: List[OptionListItem] = []


class Model(BaseModel):
    result: Result
