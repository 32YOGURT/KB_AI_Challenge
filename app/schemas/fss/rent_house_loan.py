from __future__ import annotations

from typing import Any, List

from pydantic import BaseModel


class BaseListItem(BaseModel):
    dcls_month: str
    fin_co_no: str
    fin_prdt_cd: str
    kor_co_nm: str
    fin_prdt_nm: str
    join_way: str
    loan_inci_expn: str
    erly_rpay_fee: str
    dly_rate: str
    loan_lmt: str
    dcls_strt_day: str
    dcls_end_day: Any
    fin_co_subm_day: str


class OptionListItem(BaseModel):
    dcls_month: str
    fin_co_no: str
    fin_prdt_cd: str
    mrtg_type: str | None = None
    mrtg_type_nm: str | None = None
    rpay_type: str
    rpay_type_nm: str
    lend_rate_type: str
    lend_rate_type_nm: str
    lend_rate_min: float
    lend_rate_max: float
    lend_rate_avg: float | None = None


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
