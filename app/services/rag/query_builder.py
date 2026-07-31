"""RAG 검색 쿼리를 결정론적으로 생성한다 (LLM 호출 없음). 3계층으로 구성한다:

1. 일반 축 — 상품 카테고리(예금/적금/대출/카드)별 고정 위험 축. 특약/기본약관/약정서에서
   검색한다 — 중도해지/예금자보호 같은 위험 조건은 대개 이 문서들에 있다.
2. 상품설명서 축 — 금리/가입조건 같은 사실 정보. 상품설명서에서만 검색한다 — 실제 상품
   자료(금리 %, 우대조건 목록)를 리포트에 반영하기 위한 축이다.
3. 유저특화 축 — 유저 마이데이터 신호가 특정 임계값을 넘을 때만 추가되는 축(문서 종류
   제한 없음). 예: 유동성 부족 -> 중도해지 축 추가, 예금자보호 한도초과 -> 그 축 추가.

이전에는 이 축 선택을 gpt-4o-mini에 맡겼으나, 요청마다 LLM 왕복이 하나 늘어 지연시간이
커졌다. 유저특화 축은 결국 "신호 임계값 -> 정해진 키워드" 매핑이라 LLM 없이도 표현 가능해서
결정론적 방식으로 되돌렸다.
"""

from datetime import datetime

from app.schemas import SearchQuery, UserSignals
from app.schemas.check import CheckSubject

_RISK_DOC_TYPES = ["특약", "기본약관", "약정서"]
_DESCRIPTION_DOC_TYPES = ["상품설명서"]

_CATEGORY_AXIS_TEMPLATES: dict[str, list[str]] = {
    "예금": [
        "중도해지 중도해지이율 중도해지수수료",
        "만기 만기해지 만기후이율",
        "예금자보호 보호한도",
        "유의사항 제한사항 수수료",
    ],
    "적금": [
        "우대금리 우대이율 조건 미달",
        "중도해지 중도해지이율 특별중도해지",
        "만기 만기해지 만기후이율",
        "예금자보호 보호한도",
    ],
    "대출": [
        "중도상환수수료 조기상환",
        "변동금리 금리인상 연체이자",
        "상환조건 유의사항",
    ],
    "카드": [
        "연회비 갱신",
        "부가서비스 조건 실적",
        "유의사항 해지",
    ],
}
_DEFAULT_AXES = ["유의사항 조건 수수료"]

_DESCRIPTION_AXES = [
    "기본정보 가입대상 가입기간 가입금액",
    "금리 우대이율 우대조건",
]

_LOW_BALANCE_THRESHOLD = 500_000
_MATURITY_SOON_DAYS = 30


def _general_queries(category: str) -> list[SearchQuery]:
    axes = _CATEGORY_AXIS_TEMPLATES.get(category, _DEFAULT_AXES)
    return [SearchQuery(text=axis, doc_types=_RISK_DOC_TYPES) for axis in axes]


def _description_queries() -> list[SearchQuery]:
    return [SearchQuery(text=axis, doc_types=_DESCRIPTION_DOC_TYPES) for axis in _DESCRIPTION_AXES]


def _user_specific_queries(signals: UserSignals) -> list[SearchQuery]:
    queries: list[SearchQuery] = []
    liquidity = signals.liquidity
    dist = signals.asset_distribution

    if liquidity.balance_amt < _LOW_BALANCE_THRESHOLD or liquidity.recent_net_cash_flow < 0:
        queries.append(SearchQuery(text="중도해지 중도해지이율 긴급출금"))

    if any(inst.is_over_protection_limit for inst in dist.by_institution):
        queries.append(SearchQuery(text="예금자보호 보호한도"))

    today = datetime.now()
    if any(
        0 <= (datetime.strptime(m.exp_date, "%Y%m%d") - today).days <= _MATURITY_SOON_DAYS
        for m in dist.upcoming_maturities
    ):
        queries.append(SearchQuery(text="만기 만기해지 만기후이율 자동재예치"))

    transit = next((c for c in signals.card_category.by_category if c.category == "대중교통"), None)
    if transit is None or transit.count == 0:
        queries.append(SearchQuery(text="실적조건 대중교통 이용실적 우대금리 조건"))

    return queries


def build_search_queries(subject: CheckSubject, signals: UserSignals) -> list[SearchQuery]:
    return (
        _general_queries(subject.category)
        + _description_queries()
        + _user_specific_queries(signals)
    )
