from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel


class BaseListItem(BaseModel):
    dcls_month: str
    fin_co_no: str
    fin_prdt_cd: str
    kor_co_nm: str
    fin_prdt_nm: str
    join_way: str
    mtrt_int: str
    spcl_cnd: str
    join_deny: str
    join_member: str
    etc_note: str
    max_limit: Optional[int]
    dcls_strt_day: str
    dcls_end_day: Any
    fin_co_subm_day: str


class OptionListItem(BaseModel):
    dcls_month: str
    fin_co_no: str
    fin_prdt_cd: str
    intr_rate_type: str
    intr_rate_type_nm: str
    save_trm: str
    intr_rate: float
    intr_rate2: float


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
