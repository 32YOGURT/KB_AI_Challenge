"""RAG 검색 쿼리를 gpt-4o-mini로 생성한다. 카테고리별 위험 축(우대조건/중도해지/만기/
예금자보호 등)으로 나눠 쿼리를 만드는 건 이전과 같지만, 이제 유저 마이데이터 신호(유동성/
자산분포)를 프롬프트에 함께 넣어서 검색 자체를 유저별로 개인화한다 — 예: 유동성이 부족한
유저는 중도해지 축을 더 구체적으로, 예금자보호 한도를 넘은 유저는 그 축을 우선한다.

결정적 dict 조회(이전 방식)에서 LLM 호출로 바꾸면서 지연시간이 늘어나는 건 감수하기로
했다 — 이 프로젝트의 차별점(선제적 트리거 + 유저 데이터 자동 결합)이 검색 단계부터
반영되는 게, 검색 속도보다 우선순위가 높다고 판단함.

_CATEGORY_AXIS_TEMPLATES는 삭제하지 않고 두 가지로 재사용한다:
1. LLM 프롬프트에 few-shot 예시로 포함 — 실측된 어휘 불일치 문제(코퍼스는 "우대이율"을
   쓰는데 "우대금리"로 검색하면 새는 식) 때문에, LLM이 맨땅에서 용어를 지어내지 않고
   실제 약관 어휘체에 앵커링하게 하기 위함.
2. LLM 호출 실패(API 에러/타임아웃/스키마 검증 실패) 시 폴백 — 쿼리 생성 실패가 리스크
   체크 전체를 막지 않게 함.
"""

import json

from app.clients.openai_client import get_client
from app.schemas import UserSignals
from app.schemas.check import CheckSubject
from app.services.rag.llm_inference import format_signals

LLM_MODEL = "gpt-4o-mini"

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

_QUERIES_SCHEMA = {
    "name": "search_queries",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "queries": {
                "type": "array",
                "minItems": 3,
                "maxItems": 6,
                "items": {"type": "string"},
                "description": "약관 검색용 짧은 키워드형 쿼리 목록. 각 쿼리는 서로 다른 위험 축을 겨냥한다.",
            }
        },
        "required": ["queries"],
        "additionalProperties": False,
    },
}

_SYSTEM_PROMPT = """당신은 'Fin-Guard AI'의 RAG 검색 쿼리 생성기입니다. 가입 직전 소비자에게
위험성을 경고하기 위해, 이 상품의 약관/특약/상품설명서에서 검색해야 할 위험 축을 결정하고
각 축마다 짧은 키워드형 검색 쿼리를 만드세요.

규칙:
1. 쿼리는 문장이 아니라 약관에 실제로 쓰이는 단어를 나열한 짧은 키워드 조합입니다
   (예: "중도해지 중도해지이율 특별중도해지"). 아래 [카테고리별 예시]가 실제 약관 어휘체를
   반영한 참고 자료이니, 여기서 벗어난 표현을 지어내지 말고 이 어휘체를 우선 따르세요.
2. [유저 데이터]에 특이 신호가 있으면 관련 축을 우선하거나 더 구체적으로 만드세요:
   - 유동성이 부족하거나 최근 순현금흐름이 마이너스면 → 중도해지/긴급 출금 관련 축을 강화
   - 특정 금융사 잔액이 예금자보호 한도를 초과했으면 → 예금자보호 축을 강화
   - 만기 임박 상품이 있으면 → 만기/자동재예치 관련 축을 강화
   - 특이 신호가 없으면 [카테고리별 예시]와 비슷한 수준의 일반적인 축 구성을 사용하세요.
3. 쿼리는 3~6개, 서로 다른 위험 축을 겨냥해야 합니다(같은 축을 표현만 바꿔 중복 생성 금지).

[카테고리별 예시]
{examples}
"""


def _fallback_queries(category: str) -> list[str]:
    return _CATEGORY_AXIS_TEMPLATES.get(category, _DEFAULT_AXES)


def build_search_queries(subject: CheckSubject, signals: UserSignals) -> list[str]:
    examples = "\n".join(
        f"- {category}: {', '.join(axes)}" for category, axes in _CATEGORY_AXIS_TEMPLATES.items()
    )
    user_prompt = (
        f"[상품 정보]\n{subject.bank} {subject.name} ({subject.category})\n\n"
        f"[유저 데이터]\n{format_signals(signals)}"
    )

    try:
        response = get_client().chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT.format(examples=examples)},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_schema", "json_schema": _QUERIES_SCHEMA},
        )
        queries = json.loads(response.choices[0].message.content)["queries"]
        if not queries:
            raise ValueError("빈 쿼리 목록")
        return queries
    except Exception:  # noqa: BLE001 - 쿼리 생성 실패가 리스크체크 전체를 막지 않게 정적 템플릿으로 폴백
        return _fallback_queries(subject.category)
