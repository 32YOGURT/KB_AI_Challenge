from typing import Literal

from pydantic import BaseModel


class ProductCondition(BaseModel):
    id: str
    severity: Literal["RED", "YELLOW"]
    field: str
    operator: Literal["lt", "lte", "gt", "gte", "eq"]
    threshold: float
    headline: str
    summary_lines: list[str]
    basis_clause: str
    basis_source: str


class Product(BaseModel):
    id: str
    name: str
    bank: str
    category: str
    headline_rate: str
    base_rate: float
    max_preferential_rate: float
    min_period_months: int
    description: str
    risk_conditions: list[ProductCondition] = []


class ProductSummary(BaseModel):
    id: str
    name: str
    bank: str
    category: str
    headline_rate: str
    description: str
