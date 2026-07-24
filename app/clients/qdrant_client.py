from functools import lru_cache

from qdrant_client import QdrantClient

from app.config import QDRANT_URL


@lru_cache
def get_client() -> QdrantClient:
    return QdrantClient(url=QDRANT_URL)
