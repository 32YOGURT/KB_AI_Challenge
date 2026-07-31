"""RAG 검색/색인. 조항(제N조) 단위로 청킹된 ClauseChunk를 Qdrant `product_clauses`
컬렉션에 저장하고, product_id 전용 문서 + company 공통 문서(기본약관 등)를 함께 검색한다.
"""

import uuid
from functools import lru_cache

from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    IsNullCondition,
    MatchValue,
    PayloadField,
    PointStruct,
    VectorParams,
)

from app.clients.qdrant_client import get_client
from app.schemas import ClauseChunk, ClauseSearchResult
from app.services.rag.embeddings import EMBEDDING_DIM, embed_text, embed_texts

COLLECTION_NAME = "product_clauses"


def ensure_collection() -> None:
    client = get_client()
    try:
        client.get_collection(COLLECTION_NAME)
    except UnexpectedResponse as exc:
        if exc.status_code != 404:
            raise
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
        )


def upsert_clauses(chunks: list[ClauseChunk]) -> None:
    """chunk.content_hash로부터 결정적 point id를 만들어서, 같은 내용을 다시 넣어도
    중복 생성 없이 upsert(덮어쓰기)되게 한다."""
    ensure_collection()
    vectors = embed_texts([chunk.text for chunk in chunks])
    points = [
        PointStruct(
            id=str(uuid.uuid5(uuid.NAMESPACE_URL, chunk.content_hash)),
            vector=vector,
            payload=chunk.model_dump(),
        )
        for chunk, vector in zip(chunks, vectors, strict=True)
    ]
    get_client().upsert(collection_name=COLLECTION_NAME, points=points)


# query_builder가 이제 유저 신호를 반영해 쿼리를 LLM으로 동적 생성하므로, 쿼리 문자열이
# 더 이상 고정 집합이 아니다 — 캐시 히트율은 낮아지지만(요청마다 문구가 조금씩 다를 수
# 있음), 우연히 같은 문구가 재사용되는 경우(폴백 시 정적 템플릿, 또는 LLM이 비슷한 유저
# 상황에 비슷한 쿼리를 생성하는 경우)엔 여전히 임베딩 API 호출을 아낄 수 있어 캐시 자체는
# 유지한다.
_embed_query = lru_cache(maxsize=64)(embed_text)


def search_clauses(product_id: str, company: str, query: str, top_k: int = 5) -> list[ClauseSearchResult]:
    """product_id 전용 문서 + company 공통 문서(기본약관 등)를 함께 검색한다.

    컬렉션이 아직 색인되지 않은 경우(RAG miss) 빈 리스트를 반환한다 — 호출부(LLM 추론)가
    이를 "근거 조항 없음"으로 처리한다.
    """
    vector = _embed_query(query)
    try:
        results = get_client().query_points(
            collection_name=COLLECTION_NAME,
            query=vector,
            query_filter=Filter(
                must=[FieldCondition(key="company", match=MatchValue(value=company))],
                should=[
                    FieldCondition(key="product_id", match=MatchValue(value=product_id)),
                    IsNullCondition(is_null=PayloadField(key="product_id")),
                ],
            ),
            limit=top_k,
            with_payload=True,
        ).points
    except UnexpectedResponse as exc:
        if exc.status_code == 404:
            return []
        raise

    return [ClauseSearchResult(**point.payload, score=point.score) for point in results]


def search_clauses_multi(
    product_id: str, company: str, queries: list[str], top_k_per_query: int = 2
) -> list[ClauseSearchResult]:
    """위험 축마다(query_builder.build_search_queries) 개별로 search_clauses를 돌리고 병합한다.

    같은 조항이 여러 축에 걸리는 경우가 실제로 있다(예: "중도해지이율 및 만기후이율"
    조항은 중도해지 축과 만기 축 양쪽에 매치될 수 있음). content_hash로 dedup하고,
    겹치면 더 높은 점수 쪽을 남긴다. 최종 정렬은 점수 내림차순.
    """
    best: dict[str, ClauseSearchResult] = {}
    for query in queries:
        for result in search_clauses(product_id=product_id, company=company, query=query, top_k=top_k_per_query):
            existing = best.get(result.content_hash)
            if existing is None or result.score > existing.score:
                best[result.content_hash] = result
    return sorted(best.values(), key=lambda r: r.score, reverse=True)
