from __future__ import annotations

from typing import Any, List

from pydantic import BaseModel


class BaseListItem(BaseModel):
    dcls_month: str
    fin_co_no: str
    fin_prdt_cd: str
    kor_co_nm: str
    fin_prdt_nm: str
    fin_prdt_type: str
    fin_prdt_type_nm: str
    loan_type: str
    rpay_type: str
    lend_rate_type: str
    join_way: str
    use_way: str
    loan_limit: str
    loan_limit_detl: str
    join_deny: str
    join_deny_detl: str | None = None
    spcl_rate: Any
    loan_term: str
    erly_rpay_fee: str
    loan_inci_expn: str
    dly_rate: str
    dcls_strt_day: str
    dcls_end_day: Any
    fin_co_subm_day: str


class OptionListItem(BaseModel):
    dcls_month: str
    fin_co_no: str
    fin_prdt_cd: str
    val1_grad_1: float | None = None
    val1_grad_2: float | None = None
    val1_grad_3: float | None = None
    val1_grad_4: float | None = None
    val1_grad_5: float | None = None
    val1_grad_6: float | None = None
    val1_grad_7: float | None = None
    val1_grad_8: float | None = None
    val1_grad_avg: float | None = None
    val2_grad_1: float | None = None
    val2_grad_2: float | None = None
    val2_grad_3: float | None = None
    val2_grad_4: float | None = None
    val2_grad_5: float | None = None
    val2_grad_6: float | None = None
    val2_grad_7: float | None = None
    val2_grad_8: float | None = None
    val2_grad_avg: float | None = None
    val3_grad_1: float | None = None
    val3_grad_2: float | None = None
    val3_grad_3: float | None = None
    val3_grad_4: float | None = None
    val3_grad_5: float | None = None
    val3_grad_6: float | None = None
    val3_grad_7: float | None = None
    val3_grad_8: float | None = None
    val3_grad_avg: float | None = None
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
