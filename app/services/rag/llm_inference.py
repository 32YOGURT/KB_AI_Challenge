"""RAG로 검색된 조항 + 유저 데이터를 결합해 gpt-4o-mini에 구조화된 위험성 판정을 요청한다."""

import json

from app.clients.openai_client import get_client
from app.schemas import MatchedClause, UserSignals
from app.schemas.check import CheckSubject

LLM_MODEL = "gpt-4o-mini"

_RISK_REPORT_SCHEMA = {
    "name": "risk_report",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "points": {
                "type": "array",
                "minItems": 3,
                "maxItems": 6,
                "description": "가입 전 팩트체크 포인트(위험 경고 또는 상품 정보). 3~6개. 각 포인트는 한 줄 헤드라인과 구체적 설명, 그 판단의 근거가 된 약관 조항의 번호(있으면)를 함께 담는다.",
                "items": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "enum": ["description", "risk"],
                            "description": "이 포인트의 종류. 상품 정보(위험이 아닌 사실)면 description, 놓치기 쉬운 불이익이면 risk.",
                        },
                        "text": {
                            "type": "string",
                            "description": "사회 초년생도 바로 이해할 수 있는 한 줄 헤드라인 (15~30자 내외)",
                        },
                        "detail": {
                            "type": "string",
                            "description": "text를 뒷받침하는 2~3문장의 구체적 설명. 조항의 실제 조건/숫자(금리, 한도, 기간 등)와 [유저 소비/자산 데이터]의 실제 수치를 함께 언급해, 이 유저에게 왜 해당되는지가 드러나게 쓴다. 일반론으로 뭉뚱그리지 않는다.",
                        },
                        "clause_index": {
                            "type": ["integer", "null"],
                            "description": "이 포인트 판단의 근거가 된 [약관 조항] 목록의 번호(1부터 시작). 근거가 되는 조항이 목록에 없으면 null.",
                        },
                        "evidence_quote": {
                            "type": ["string", "null"],
                            "description": "clause_index가 가리키는 조항 원문에서 한 글자도 바꾸지 않고 그대로 가져온 10~40자 내외의 핵심 문장/구절. 요약하거나 다른 말로 바꿔쓰지 않는다. clause_index가 null이면 이것도 null.",
                        },
                    },
                    "required": ["type", "text", "detail", "clause_index", "evidence_quote"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["points"],
        "additionalProperties": False,
    },
}

_TIER_LABELS = {"general": "일반위험", "description": "상품설명서", "user_specific": "유저특화"}

_SYSTEM_PROMPT = """당신은 금융 상품 가입 직전 소비자를 위한 팩트체크 엔진입니다.
주어진 [약관 조항]과 [유저 소비/자산 데이터]만 근거로, 이 유저가 이 상품에 가입하기 전에
알아야 할 사실을 포인트 목록으로 정리하세요. 포인트는 두 종류를 섞어서 냅니다:
- 위험 경고: 놓치기 쉬운 불이익(중도해지, 조건 미달, 예금자보호 한도 등)
- 상품 정보: 위험은 아니지만 알아야 할 핵심 조건(금리, 가입조건 등)

[약관 조항] 각 항목 앞에는 (유형/검색축/검색된 이유) 라벨이 붙어 있습니다:
- 유형이 특약/기본약관/약정서인 조항: risk 포인트의 근거로 우선 사용하세요.
- 유형이 상품설명서인 조항: description 포인트의 근거로 사용하세요 — 포인트 중 최소 1개는
  상품설명서 조항을 근거로 한 description 포인트여야 합니다.
- 검색축이 "유저특화"이고 "검색된 이유"가 적힌 조항: 그 이유에 있는 유저의 실제 수치를
  detail에 그대로 반영해, 왜 이 유저에게 해당되는지가 명확히 드러나게 쓰세요.

규칙:
1. 반드시 risk_report JSON 스키마에 맞춰서만 응답한다. 다른 텍스트는 출력하지 않는다.
2. 포인트는 반드시 3~6개를 낸다. 검색된 조항이 적으면 일반적으로 알아둘 만한 상품 정보
   포인트를 추가해서라도 최소 3개를 채우고, 근거가 겹치지 않는 서로 다른 포인트 위주로
   6개를 넘기지 않는다.
3. 각 포인트의 type은 description 또는 risk 중 하나다. 상품 정보면 description, 놓치기 쉬운
   불이익이면 risk로 정확히 표시한다.
4. 각 포인트의 clause_index는 [약관 조항] 목록 앞에 붙은 번호([1], [2], ...) 중 하나를 그대로 고른다. 조항 제목이나 내용을 직접 쓰지 않으며, 목록에 없는 번호를 지어내지 않는다.
5. 해당 포인트의 근거가 되는 조항을 목록에서 찾을 수 없으면 그 포인트의 clause_index는 null로 둔다.
6. text는 한 줄 헤드라인이다(15~30자 내외, 핵심만).
7. detail은 text를 뒷받침하는 2~3문장이다 — 조항의 구체적 조건/숫자와 [유저 소비/자산 데이터]의 실제 수치를 함께 언급해 "왜 이 유저에게 해당되는지"를 설명한다. "불이익이 있을 수 있습니다" 같은 일반론만 쓰지 않는다. 숫자는 [약관 조항]과 [유저 소비/자산 데이터]에 적힌 그대로 옮겨 적고, 계산하거나 자릿수를 바꿔 쓰지 않는다.
8. clause_index가 null이 아니면, evidence_quote에 그 조항 원문에서 한 글자도 바꾸지 않고 그대로
   가져온 10~40자 내외의 핵심 문장/구절을 담는다. 요약하거나 의역하지 않는다. clause_index가
   null이면 evidence_quote도 null로 둔다.
"""


def _format_clauses(matches: list[MatchedClause]) -> str:
    if not matches:
        return "(검색된 약관 조항 없음)"
    # 번호는 LLM이 clause_index로 되짚을 수 있게 붙인다 — 호출부(pipeline)가 이 번호로
    # 원본 조항을 찾아 출처/페이지를 결정론적으로 채운다. 검색축/이유를 라벨로 붙여서
    # "이 조항이 왜 검색됐는지"를 LLM이 추론하지 않고 그대로 전달받게 한다.
    lines = []
    for i, m in enumerate(matches, start=1):
        c = m.clause
        tiers = "/".join(_TIER_LABELS[t] for t in m.tiers)
        reason = f" | 검색된 이유: {'; '.join(m.reasons)}" if m.reasons else ""
        lines.append(
            f"[{i}] (유형: {c.doc_type} | 검색축: {tiers}{reason} | "
            f"출처: {c.source}{f' {c.page}p' if c.page else ''}) {c.clause_title}\n{c.text}"
        )
    return "\n\n".join(lines)


def format_signals(signals: UserSignals) -> str:
    liquidity = signals.liquidity
    dist = signals.asset_distribution
    card_category = signals.card_category

    institutions = "\n".join(
        f"  - {inst.org_code}: 잔액 {inst.total_balance:,.0f}원"
        + ("(예금자보호 한도 초과)" if inst.is_over_protection_limit else "")
        for inst in dist.by_institution
    ) or "  - 연동된 예금/적금 상품 없음"

    maturities = "\n".join(
        f"  - {m.org_code} {m.prod_name}: 만기 {m.exp_date}" for m in dist.upcoming_maturities
    ) or "  - 없음"

    categories = "\n".join(
        f"  - {c.category}: {c.count}건 ({c.total_amt:,.0f}원)" for c in card_category.by_category
    ) or "  - 카드 승인내역 없음"

    return (
        f"- 총 잔액(유동자산): {liquidity.balance_amt:,.0f}원 "
        f"(출금가능액 {liquidity.withdrawable_amt:,.0f}원)\n"
        f"- 최근 순현금흐름: {liquidity.recent_net_cash_flow:,.0f}원 "
        f"(최근 거래 {liquidity.transaction_count}건)\n"
        f"- 금융사별 자산 분포:\n{institutions}\n"
        f"- 만기 예정 상품:\n{maturities}\n"
        f"- 카드 승인내역 카테고리별 집계:\n{categories}"
    )


def infer_risk_report(subject: CheckSubject, signals: UserSignals, clauses: list[MatchedClause]) -> dict:
    """약관 조항 + 유저 마이데이터 신호를 결합해 LLM에 위험성 판정을 요청하고, 파싱된 JSON을 반환한다."""
    user_prompt = (
        f"[상품 정보]\n{subject.bank} {subject.name} ({subject.category})\n\n"
        f"[유저 소비/자산 데이터]\n{format_signals(signals)}\n\n"
        f"[약관 조항 (RAG 검색 결과)]\n{_format_clauses(clauses)}"
    )

    response = get_client().chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_schema", "json_schema": _RISK_REPORT_SCHEMA},
    )

    return json.loads(response.choices[0].message.content)
