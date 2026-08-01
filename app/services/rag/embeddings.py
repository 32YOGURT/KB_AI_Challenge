from functools import lru_cache

import tiktoken

from app.clients.openai_client import get_client

EMBEDDING_MODEL = "text-embedding-3-large"
EMBEDDING_DIM = 3072

# 한 번의 embeddings 요청에 담을 텍스트 개수. 색인 시 청크당 1회씩 호출하면 왕복 지연이
# 그대로 누적되므로(수천 청크면 수십 분) 배치로 묶는다. 배치 크기는 요청당 총 토큰 상한에
# 걸리지 않을 만큼 보수적으로 잡았다 — 약관 청크가 평균 2~3천 토큰이라 32개면 10만 토큰 정도.
EMBEDDING_BATCH_SIZE = 32

# OpenAI 임베딩 API의 입력 1건당 토큰 상한(공식 문서 기준 8192)보다 여유를 두고 낮게 잡는다
# — 정확히 8192에 맞춰 자르면 근소한 계산 차이로 여전히 넘는 경우가 생길 수 있어서다.
MAX_EMBED_TOKENS = 8000

@lru_cache
def _get_encoding():
    """tiktoken은 인코딩 파일을 원격에서 받아 캐시한다 — 임포트 시점에 받으면 네트워크
    실패가 앱 기동 자체를 막으므로 첫 사용까지 미룬다."""
    return tiktoken.encoding_for_model(EMBEDDING_MODEL)


def split_for_embedding(text: str) -> list[str]:
    """text가 MAX_EMBED_TOKENS를 넘으면 여러 조각으로 쪼갠다.

    청킹 전략(제N조/heading 단위)이 이미 의미 단위로 잘라두므로 대부분의 청크는 그대로
    한 조각으로 반환된다 — 이건 "그래도 한 조각이 너무 큰" 드문 케이스(예: heading 하나에
    거대한 표가 통째로 붙은 경우)를 막는 안전망이다.

    줄 단위로 그리디하게 묶어서 자르고, 한 줄 자체가 상한을 넘는 극단적인 경우에만 그 줄을
    토큰 단위로 강제 분할한다.
    """
    encoding = _get_encoding()
    if len(encoding.encode(text)) <= MAX_EMBED_TOKENS:
        return [text]

    parts: list[str] = []
    current: list[str] = []
    current_tokens = 0
    for line in text.split("\n"):
        line_token_ids = encoding.encode(line)
        if len(line_token_ids) > MAX_EMBED_TOKENS:
            if current:
                parts.append("\n".join(current))
                current, current_tokens = [], 0
            for i in range(0, len(line_token_ids), MAX_EMBED_TOKENS):
                parts.append(encoding.decode(line_token_ids[i : i + MAX_EMBED_TOKENS]))
            continue
        if current and current_tokens + len(line_token_ids) > MAX_EMBED_TOKENS:
            parts.append("\n".join(current))
            current, current_tokens = [], 0
        current.append(line)
        current_tokens += len(line_token_ids)
    if current:
        parts.append("\n".join(current))
    return parts


def embed_texts(texts: list[str]) -> list[list[float]]:
    """여러 텍스트를 배치로 임베딩한다. 입력 순서와 동일한 순서로 벡터를 반환한다."""
    client = get_client()
    vectors: list[list[float]] = []
    for start in range(0, len(texts), EMBEDDING_BATCH_SIZE):
        batch = texts[start : start + EMBEDDING_BATCH_SIZE]
        response = client.embeddings.create(model=EMBEDDING_MODEL, input=batch)
        # API가 순서를 보장하지만 index로 정렬해 한 번 더 확실히 맞춘다.
        vectors.extend(item.embedding for item in sorted(response.data, key=lambda d: d.index))
    return vectors


def embed_text(text: str) -> list[float]:
    return embed_texts([text])[0]
