from typing import Literal

from pydantic import BaseModel


class CheckRequest(BaseModel):
    product_id: str
    user_id: str


class RiskBasis(BaseModel):
    clause: str
    source: str


class CheckResponse(BaseModel):
    product_id: str
    product_name: str
    user_id: str
    risk_level: Literal["RED", "YELLOW", "GREEN"]
    headline: str
    summary_lines: list[str]
    basis: list[RiskBasis]
