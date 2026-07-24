from __future__ import annotations

from typing import List

from pydantic import BaseModel


class BaseListItem(BaseModel):
    dcls_month: str
    fin_co_no: str
    kor_co_nm: str
    dcls_chrg_man: str
    homp_url: str
    cal_tel: str


class OptionListItem(BaseModel):
    dcls_month: str
    fin_co_no: str
    area_cd: str
    area_nm: str
    exis_yn: str


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
