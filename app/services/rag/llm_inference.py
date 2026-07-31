"""RAG로 검색된 조항 + 유저 데이터를 결합해 gpt-4o-mini에 구조화된 위험성 판정을 요청한다."""

import json

from app.clients.openai_client import get_client
from app.schemas import ClauseChunk, UserSignals
from app.schemas.check import CheckSubject

LLM_MODEL = "gpt-4o-mini"

_RISK_REPORT_SCHEMA = {
    "name": "risk_report",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "risk_level": {"type": "string", "enum": ["RED", "YELLOW", "GREEN"]},
            "points": {
                "type": "array",
                "description": "정확히 3개로 구성된 위험성 팩트체크 포인트. 각 포인트는 문장 설명과, 그 판단의 근거가 된 약관 조항(있으면)을 함께 담는다.",
                "items": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "사회 초년생도 바로 이해할 수 있는 쉬운 문장 설명"},
                        "basis": {
                            "anyOf": [
                                {
                                    "type": "object",
                                    "properties": {
                                        "clause": {"type": "string"},
                                        "source": {"type": "string"},
                                    },
                                    "required": ["clause", "source"],
                                    "additionalProperties": False,
                                },
                                {"type": "null"},
                            ],
                            "description": "이 포인트 판단의 근거가 된 약관 조항. 제공된 컨텍스트에 실제로 존재하는 조항만 인용하며, 근거가 없으면 null.",
                        },
                    },
                    "required": ["text", "basis"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["risk_level", "points"],
        "additionalProperties": False,
    },
}

_SYSTEM_PROMPT = """당신은 'Fin-Guard AI'로, 금융 상품 가입 직전 소비자를 보호하는 위험성 팩트체크 엔진입니다.
주어진 [약관 조항]과 [유저 소비/자산 데이터]만 근거로 삼아, 이 유저가 이 상품에 가입할 때 놓치기 쉬운 위험을 판단하세요.

규칙:
1. 반드시 risk_report JSON 스키마에 맞춰서만 응답한다. 다른 텍스트는 출력하지 않는다.
2. 각 포인트의 basis에 인용하는 조항은 반드시 제공된 [약관 조항] 컨텍스트에 실제로 존재하는 내용만 사용한다. 컨텍스트에 없는 조항을 지어내거나 추측하지 않는다.
3. 해당 포인트의 근거가 되는 조항을 컨텍스트에서 찾을 수 없으면 그 포인트의 basis는 null로 둔다. 모든 포인트의 근거를 찾을 수 없으면 risk_level은 GREEN으로 판단한다.
4. points는 정확히 3개, 각 text는 사회 초년생도 바로 이해할 수 있는 쉬운 문장으로 작성한다.
5. risk_level 기준: RED는 중도해지 페널티/원금 손실 등 심각한 금전적 손해, YELLOW는 우대조건 미달 등 기대보다 낮은 혜택, GREEN은 특이 위험 없음.
"""


def _format_clauses(clauses: list[ClauseChunk]) -> str:
    if not clauses:
        return "(검색된 약관 조항 없음)"
    return "\n\n".join(
        f"[출처: {c.source}{f' {c.page}p' if c.page else ''}] {c.clause_title}\n{c.text}"
        for c in clauses
    )


def format_signals(signals: UserSignals) -> str:
    liquidity = signals.liquidity
    dist = signals.asset_distribution

    institutions = "\n".join(
        f"  - {inst.org_code}: 잔액 {inst.total_balance:,.0f}원"
        + ("(예금자보호 한도 초과)" if inst.is_over_protection_limit else "")
        for inst in dist.by_institution
    ) or "  - 연동된 예금/적금 상품 없음"

    maturities = "\n".join(
        f"  - {m.org_code} {m.prod_name}: 만기 {m.exp_date}" for m in dist.upcoming_maturities
    ) or "  - 없음"

    return (
        f"- 총 잔액(유동자산): {liquidity.balance_amt:,.0f}원 "
        f"(출금가능액 {liquidity.withdrawable_amt:,.0f}원)\n"
        f"- 최근 순현금흐름: {liquidity.recent_net_cash_flow:,.0f}원 "
        f"(최근 거래 {liquidity.transaction_count}건)\n"
        f"- 금융사별 자산 분포:\n{institutions}\n"
        f"- 만기 예정 상품:\n{maturities}"
    )


def infer_risk_report(subject: CheckSubject, signals: UserSignals, clauses: list[ClauseChunk]) -> dict:
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
