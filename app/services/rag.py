"""RAG 검색/색인. 조항(제N조) 단위로 청킹된 ClauseChunk를 Qdrant `product_clauses`
컬렉션에 저장하고, product_id 전용 문서 + company 공통 문서(기본약관 등)를 함께 검색한다.
"""

import uuid

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
from app.services.embeddings import EMBEDDING_DIM, embed_text

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
    points = [
        PointStruct(
            id=str(uuid.uuid5(uuid.NAMESPACE_URL, chunk.content_hash)),
            vector=embed_text(chunk.text),
            payload=chunk.model_dump(),
        )
        for chunk in chunks
    ]
    get_client().upsert(collection_name=COLLECTION_NAME, points=points)


def search_clauses(product_id: str, company: str, query: str, top_k: int = 5) -> list[ClauseSearchResult]:
    """product_id 전용 문서 + company 공통 문서(기본약관 등)를 함께 검색한다.

    컬렉션이 아직 색인되지 않은 경우(RAG miss) 빈 리스트를 반환한다 — 호출부(LLM 추론)가
    이를 "근거 조항 없음"으로 처리한다.
    """
    vector = embed_text(query)
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
