"""RAG 검색/색인. 조항(제N조) 단위로 청킹된 ClauseChunk를 Qdrant `product_clauses`
컬렉션에 저장하고, product_id 전용 문서 + company 공통 문서(기본약관 등)를 함께 검색한다.

dense(의미 유사도) 벡터와 sparse(BM25류 정확 용어 매칭) 벡터를 한 컬렉션에 함께 저장하고,
검색 시 RRF로 융합하는 하이브리드 구조다 — 순수 dense는 "예금자보호", "질권설정" 같은
정확한 전문용어를 놓치는 사례가 실측으로 확인됐다. dense만 쓰는 검색도 비교 측정용으로
남겨뒀다(search_clauses의 mode 인자).
"""

import uuid
from functools import lru_cache
from typing import Literal

from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    Fusion,
    FusionQuery,
    IsNullCondition,
    MatchAny,
    MatchValue,
    Modifier,
    PayloadField,
    PointStruct,
    Prefetch,
    SparseVectorParams,
    VectorParams,
)

from app.clients.qdrant_client import get_client
from app.schemas import ClauseChunk, ClauseSearchResult, SearchQuery
from app.services.rag.embeddings import EMBEDDING_DIM, embed_text, embed_texts
from app.services.rag.sparse import to_sparse_vector

COLLECTION_NAME = "product_clauses"

DENSE_VECTOR = "dense"
SPARSE_VECTOR = "sparse"

SearchMode = Literal["hybrid", "dense"]


def ensure_collection() -> None:
    client = get_client()
    try:
        client.get_collection(COLLECTION_NAME)
    except UnexpectedResponse as exc:
        if exc.status_code != 404:
            raise
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config={DENSE_VECTOR: VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE)},
            sparse_vectors_config={SPARSE_VECTOR: SparseVectorParams(modifier=Modifier.IDF)},
        )


def drop_collection() -> None:
    """컬렉션을 통째로 지운다. 벡터 스키마가 바뀌면(예: sparse 벡터 추가) 기존 컬렉션에
    그대로 upsert할 수 없어서 재생성이 필요하다 — scripts/rag/ingest.py --recreate 전용."""
    get_client().delete_collection(COLLECTION_NAME)


def upsert_clauses(chunks: list[ClauseChunk]) -> None:
    """chunk.content_hash로부터 결정적 point id를 만들어서, 같은 내용을 다시 넣어도
    중복 생성 없이 upsert(덮어쓰기)되게 한다."""
    ensure_collection()
    vectors = embed_texts([chunk.text for chunk in chunks])
    points = [
        PointStruct(
            id=str(uuid.uuid5(uuid.NAMESPACE_URL, chunk.content_hash)),
            vector={
                DENSE_VECTOR: vector,
                SPARSE_VECTOR: to_sparse_vector(chunk.text),
            },
            payload=chunk.model_dump(),
        )
        for chunk, vector in zip(chunks, vectors, strict=True)
    ]
    get_client().upsert(collection_name=COLLECTION_NAME, points=points)


# query_builder가 결정론적 템플릿/임계값으로 쿼리를 만들므로 문구 자체는 고정 집합에
# 가깝다 — 같은 카테고리/신호 조합이면 쿼리 문자열이 그대로 재사용되어 캐시 히트율이 높다.
_embed_query = lru_cache(maxsize=64)(embed_text)


def search_clauses(
    product_id: str,
    company: str,
    query: str,
    top_k: int = 5,
    mode: SearchMode = "hybrid",
    doc_types: list[str] | None = None,
) -> list[ClauseSearchResult]:
    """product_id 전용 문서 + company 공통 문서(기본약관 등)를 함께 검색한다.

    mode="hybrid"는 dense(의미)와 sparse(정확 용어) 검색을 각각 돌린 뒤 RRF로 융합한다.
    mode="dense"는 dense만 쓴다 — 하이브리드가 실제로 나은지 비교 측정하기 위해 남겨둔 경로다.

    주의: 두 mode의 score는 스케일이 전혀 다르다. dense는 코사인 유사도(대략 0.3~0.6),
    hybrid는 RRF 점수(1/(60+rank) 스케일이라 0.02 안팎)다. **mode가 다른 결과끼리 점수를
    비교하면 안 된다.** 같은 mode 안에서의 순위 비교만 의미가 있다.

    doc_types를 지정하면(예: ["상품설명서"]) 그 문서 종류에서만 검색한다 — 위험 축과
    상품설명 축을 서로 다른 문서에서 찾도록 query_builder가 지정한다.

    컬렉션이 아직 색인되지 않은 경우(RAG miss) 빈 리스트를 반환한다 — 호출부(LLM 추론)가
    이를 "근거 조항 없음"으로 처리한다.
    """
    must_conditions = [FieldCondition(key="company", match=MatchValue(value=company))]
    if doc_types:
        must_conditions.append(FieldCondition(key="doc_type", match=MatchAny(any=doc_types)))

    query_filter = Filter(
        must=must_conditions,
        should=[
            FieldCondition(key="product_id", match=MatchValue(value=product_id)),
            IsNullCondition(is_null=PayloadField(key="product_id")),
        ],
    )

    if mode == "dense":
        query_args = {"query": _embed_query(query), "using": DENSE_VECTOR}
    else:
        prefetch_limit = top_k * 4
        query_args = {
            "prefetch": [
                Prefetch(
                    query=_embed_query(query),
                    using=DENSE_VECTOR,
                    filter=query_filter,
                    limit=prefetch_limit,
                ),
                Prefetch(
                    query=to_sparse_vector(query),
                    using=SPARSE_VECTOR,
                    filter=query_filter,
                    limit=prefetch_limit,
                ),
            ],
            "query": FusionQuery(fusion=Fusion.RRF),
        }

    try:
        results = get_client().query_points(
            collection_name=COLLECTION_NAME,
            query_filter=query_filter,
            limit=top_k,
            with_payload=True,
            **query_args,
        ).points
    except UnexpectedResponse as exc:
        if exc.status_code == 404:
            return []
        raise

    return [ClauseSearchResult(**point.payload, score=point.score) for point in results]


def search_clauses_multi(
    product_id: str,
    company: str,
    queries: list[SearchQuery],
    top_k_per_query: int = 2,
    mode: SearchMode = "hybrid",
) -> list[ClauseSearchResult]:
    """위험 축마다(query_builder.build_search_queries) 개별로 search_clauses를 돌리고 병합한다.

    같은 조항이 여러 축에 걸리는 경우가 실제로 있다(예: "중도해지이율 및 만기후이율"
    조항은 중도해지 축과 만기 축 양쪽에 매치될 수 있음). content_hash로 dedup하고,
    겹치면 더 높은 점수 쪽을 남긴다. 최종 정렬은 점수 내림차순.

    모든 축이 같은 mode로 검색되므로 점수 비교/정렬은 일관된 스케일 안에서 이뤄진다
    (mode별 점수 스케일 차이는 search_clauses docstring 참고).
    """
    best: dict[str, ClauseSearchResult] = {}
    for query in queries:
        for result in search_clauses(
            product_id=product_id,
            company=company,
            query=query.text,
            top_k=top_k_per_query,
            mode=mode,
            doc_types=query.doc_types,
        ):
            existing = best.get(result.content_hash)
            if existing is None or result.score > existing.score:
                best[result.content_hash] = result
    return sorted(best.values(), key=lambda r: r.score, reverse=True)
