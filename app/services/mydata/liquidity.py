"""현금흐름 & 유동성 신호 집계.

중도해지 위험 탐지 등 유동성이 필요한 모든 판단에서 재사용 가능한 범용 집계.
특정 상품의 특정 우대조건에 종속되지 않는다 — "조건을 만족하는가"는 이 값과
조항 텍스트를 함께 받은 LLM이 판단한다.
"""

from app.clients.mydata.client import MyDataClient
from app.schemas.signals.liquidity import LiquiditySignal


def get_liquidity_signal(user_id: str) -> LiquiditySignal:
    """연동된 모든 금융회사의 계좌를 합산한 유동성 신호."""
    with MyDataClient() as client:
        balance_amt = 0.0
        withdrawable_amt = 0.0
        net_cash_flow = 0.0
        transaction_count = 0

        for org_code in client.list_institutions(user_id):
            detail = client.get_bank_account_detail(user_id, org_code)
            balance_amt += sum(item.balance_amt for item in detail.detail_list)
            withdrawable_amt += sum(item.withdrawable_amt for item in detail.detail_list)

            transactions = client.get_bank_account_transactions(user_id, org_code)
            net_cash_flow += sum(
                t.trans_amt if t.trans_type == "입금" else -t.trans_amt for t in transactions.trans_list
            )
            transaction_count += len(transactions.trans_list)

    return LiquiditySignal(
        balance_amt=balance_amt,
        withdrawable_amt=withdrawable_amt,
        recent_net_cash_flow=net_cash_flow,
        transaction_count=transaction_count,
    )
