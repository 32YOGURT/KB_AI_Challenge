from pydantic import BaseModel


class CategorySpend(BaseModel):
    category: str
    count: int
    total_amt: float


class CardCategorySignal(BaseModel):
    """가맹점명 키워드 매칭 기반 카테고리별 카드 실적 집계. 특정 상품의 실적 조건(예: 대중교통
    이용 시 우대금리) 충족 여부는 여기서 판정하지 않고, 조항 텍스트와 함께 LLM이 판단한다."""

    by_category: list[CategorySpend]
