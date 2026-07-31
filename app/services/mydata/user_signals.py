"""특정 유저에 대한 모든 마이데이터 신호를 한데 모은다. LLM 추론에 그대로 전달된다."""

from app.schemas.signals.user_signals import UserSignals
from app.services.mydata.asset_distribution import get_asset_distribution_signal
from app.services.mydata.card_category import get_card_category_signal
from app.services.mydata.liquidity import get_liquidity_signal


def get_user_signals(user_id: str) -> UserSignals:
    return UserSignals(
        user_id=user_id,
        liquidity=get_liquidity_signal(user_id),
        asset_distribution=get_asset_distribution_signal(user_id),
        card_category=get_card_category_signal(user_id),
    )
