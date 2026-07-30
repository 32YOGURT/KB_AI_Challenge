from app.clients.openai_client import get_client

EMBEDDING_MODEL = "text-embedding-3-large"
EMBEDDING_DIM = 3072

# 한 번의 embeddings 요청에 담을 텍스트 개수. 색인 시 청크당 1회씩 호출하면 왕복 지연이
# 그대로 누적되므로(수천 청크면 수십 분) 배치로 묶는다. 배치 크기는 요청당 총 토큰 상한에
# 걸리지 않을 만큼 보수적으로 잡았다 — 약관 청크가 평균 2~3천 토큰이라 32개면 10만 토큰 정도.
EMBEDDING_BATCH_SIZE = 32


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
