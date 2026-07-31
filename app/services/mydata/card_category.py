"""카드 승인내역을 가맹점명 키워드로 카테고리 분류해 집계한다.

우대금리 실적 조건(예: "대중교통 이용 시 우대금리") 충족 여부는 여기서 판정하지 않는다 —
조항 텍스트와 이 집계값을 함께 받은 LLM이 판단한다. 카테고리 목록은 특정 상품의 조건에
종속되지 않는 범용 분류다.
"""

from app.clients.mydata.client import MyDataClient
from app.schemas.signals.card_category import CardCategorySignal, CategorySpend

_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "대중교통": ["지하철", "버스", "교통공사", "티머니"],
    "택시": ["택시", "카카오T"],
    "온라인쇼핑": ["쿠팡", "네이버페이", "지마켓", "11번가"],
    "마트/편의점": ["이마트", "홈플러스", "GS25", "CU", "세븐일레븐"],
    "카페/외식": ["스타벅스", "카페", "배달의민족", "요기요"],
}


def _categorize(merchant_name: str) -> str:
    for category, keywords in _CATEGORY_KEYWORDS.items():
        if any(keyword in merchant_name for keyword in keywords):
            return category
    return "기타"


def get_card_category_signal(user_id: str) -> CardCategorySignal:
    with MyDataClient() as client:
        approvals = client.get_card_approvals(user_id).approved_list

    by_category: dict[str, CategorySpend] = {}
    for approval in approvals:
        category = _categorize(approval.merchant_name)
        spend = by_category.setdefault(category, CategorySpend(category=category, count=0, total_amt=0.0))
        spend.count += 1
        spend.total_amt += approval.approved_amt

    return CardCategorySignal(by_category=sorted(by_category.values(), key=lambda s: -s.count))
