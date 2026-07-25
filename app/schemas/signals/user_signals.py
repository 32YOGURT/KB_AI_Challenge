from pydantic import BaseModel

from app.schemas.signals.asset_distribution import AssetDistributionSignal
from app.schemas.signals.liquidity import LiquiditySignal


class UserSignals(BaseModel):
    """특정 유저에 대해 현재 시점에 모은 모든 신호. LLM 추론에 그대로 전달된다."""

    user_id: str
    liquidity: LiquiditySignal
    asset_distribution: AssetDistributionSignal
