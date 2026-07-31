"""하이브리드 검색의 sparse(BM25) 쪽. dense 임베딩을 담당하는 embeddings.py와 대칭이다.

dense 임베딩만으로는 "예금자보호", "질권설정" 같은 정확한 금융 전문용어 매칭이 약해서
(실측: 코퍼스에 분명히 있는데도 검색이 못 찾는 사례가 반복됨), 같은 컬렉션에 sparse 벡터를
함께 넣고 검색 시 RRF로 융합한다.

토크나이저로 kiwipiepy(한국어 형태소 분석)를 쓴다. 약관 텍스트는 조사가 붙은 형태로
나오는데("중도해지이율로", "질권설정을") 공백 분리로는 이게 원형과 다른 토큰이 돼버려
정확 매칭이 깨진다. 형태소 분석은 이걸 정확히 분리해준다.

Kiwi는 복합명사를 구성요소로 쪼갠다("예금자보호" -> 예금자 + 보호). 쪼갠 것만 쓰면
"보호"처럼 흔한 단어가 섞여 정확 매칭 이점이 희석되므로, **구성요소와 함께 원문에서
실제로 붙어있던 복합명사 원형도 토큰으로 넣는다**("예금자보호"). 희귀한 복합어 원형은
IDF가 높아 강한 신호가 되고, 흔한 구성요소는 IDF가 낮아 약한 신호가 되도록 Qdrant가
알아서 가중치를 잡는다.

IDF는 여기서 계산하지 않는다 — 컬렉션 전체 통계가 필요한 값이라, Qdrant 쪽에
`Modifier.IDF`를 걸어두고 서버가 계산하게 한다(retrieval.ensure_collection 참고).
여기서 만드는 값은 TF 성분뿐이다.
"""

from __future__ import annotations

import hashlib
import math
from collections import Counter
from functools import lru_cache

from qdrant_client.models import SparseVector

# 명사 계열만 남긴다. 조사/어미/접사는 검색어로서 의미가 없고, 형태소 분석이 이미 분리해준다.
# SL(외국어)은 "KB", "Star" 같은 상품명 토큰 때문에 포함한다.
_NOUN_TAGS = frozenset({"NNG", "NNP", "SL"})


@lru_cache
def _get_kiwi():
    """Kiwi 인스턴스는 모델 로딩 비용이 커서 프로세스당 한 번만 만들어 재사용한다
    (clients/qdrant_client.get_client, scripts/rag/pdf_to_markdown._get_converter와 같은 패턴)."""
    from kiwipiepy import Kiwi

    return Kiwi()


def tokenize(text: str) -> list[str]:
    """형태소 명사 토큰 + 원문에서 붙어있던 복합명사 원형을 함께 반환한다.

    복합명사 복원은 **원문에서 실제로 인접했을 때만** 한다 (토큰의 start/end로 판별).
    이게 없으면 공백으로 구분된 검색 쿼리("중도해지 특별중도해지")의 단어들까지 하나로
    붙어버린다.
    """
    tokens: list[str] = []
    run: list[str] = []  # 원문에서 연속으로 붙어있는 명사들
    prev_end = -1

    for token in _get_kiwi().tokenize(text):
        if token.tag in _NOUN_TAGS:
            if token.start != prev_end and len(run) > 1:
                # 원문에서 끊겼다 — 여기까지의 run을 복합명사로 확정하고 새 run 시작
                tokens.append("".join(run))
                run = []
            elif token.start != prev_end:
                run = []
            run.append(token.form)
            tokens.append(token.form)
            prev_end = token.end
        else:
            if len(run) > 1:
                tokens.append("".join(run))
            run = []
            prev_end = -1

    if len(run) > 1:
        tokens.append("".join(run))
    return tokens


def _token_index(token: str) -> int:
    """토큰 문자열 -> 32비트 정수 인덱스. Qdrant SparseVector가 정수 인덱스를 요구한다.
    어휘 규모(수천 개)에 비해 공간이 훨씬 커서 충돌은 무시할 수 있다."""
    return int(hashlib.sha1(token.encode("utf-8")).hexdigest()[:8], 16)


def to_sparse_vector(text: str) -> SparseVector:
    """텍스트를 sparse 벡터로 만든다. 값은 TF 성분(log(1+tf))이고 IDF는 Qdrant가 곱한다.

    log(1+tf)를 쓰는 이유: 코퍼스 전역 통계(평균 문서 길이 등)가 필요 없어 청크 하나만 보고
    독립적으로 계산할 수 있다 — upsert_clauses가 문서별로 나눠 호출되는 지금 구조와 맞는다.
    동시에 같은 단어가 반복될 때 점수가 선형으로 커지는 걸 억제한다.
    """
    counts = Counter(tokenize(text))
    indices, values = [], []
    for token, count in counts.items():
        indices.append(_token_index(token))
        values.append(math.log(1 + count))
    return SparseVector(indices=indices, values=values)
