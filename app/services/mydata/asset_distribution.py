"""금융사별 자산 분포 신호 집계.

예금자보호 초과 탐지 & 만기관리 등에서 재사용 가능한 범용 집계.
"조건을 만족하는가"의 세부 판단은 이 값과 조항 텍스트를 함께 받은 LLM이 한다.
"""

from app.clients.mydata.client import MyDataClient
from app.schemas.signals.asset_distribution import AssetDistributionSignal, InstitutionBalance, MaturityItem

DEPOSIT_PROTECTION_LIMIT = 100_000_000  # 예금자보호 한도(원)


def get_asset_distribution_signal(user_id: str) -> AssetDistributionSignal:
    """연동된 모든 금융회사에 대해 기관별 잔액 합계와 계좌별 만기일을 모은다.

    계좌 목록(은행-001)/기본정보(은행-002)/추가정보(은행-003)는 mock에서
    같은 기관의 계좌를 같은 순서로 담고 있다고 가정하고 인덱스로 대응시킨다.
    """
    with MyDataClient() as client:
        by_institution: list[InstitutionBalance] = []
        maturities: list[MaturityItem] = []

        for org_code in client.list_institutions(user_id):
            accounts = client.get_bank_accounts(user_id, org_code).account_list
            basics = client.get_bank_account_basic(user_id, org_code).basic_list
            details = client.get_bank_account_detail(user_id, org_code).detail_list

            total_balance = sum(item.balance_amt for item in details)
            by_institution.append(
                InstitutionBalance(
                    org_code=org_code,
                    total_balance=total_balance,
                    is_over_protection_limit=total_balance > DEPOSIT_PROTECTION_LIMIT,
                )
            )

            for account, basic in zip(accounts, basics):
                maturities.append(
                    MaturityItem(
                        org_code=org_code,
                        account_num=account.account_num,
                        prod_name=account.prod_name,
                        exp_date=basic.exp_date,
                    )
                )

    maturities.sort(key=lambda m: m.exp_date)

    return AssetDistributionSignal(by_institution=by_institution, upcoming_maturities=maturities)
