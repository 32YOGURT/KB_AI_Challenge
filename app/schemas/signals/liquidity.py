from pydantic import BaseModel


class LiquiditySignal(BaseModel):
    """현금흐름 & 유동성 범용 집계. 특정 상품의 특정 조건에 종속되지 않는다."""

    balance_amt: float
    withdrawable_amt: float
    recent_net_cash_flow: float
    transaction_count: int
