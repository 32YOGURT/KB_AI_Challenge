from functools import lru_cache

from qdrant_client import QdrantClient

from app.config import QDRANT_API_KEY, QDRANT_URL


@lru_cache
def get_client() -> QdrantClient:
    # 로컬 docker-compose의 Qdrant는 인증이 없어 키가 빈 값이다. 빈 문자열을 그대로 넘기면
    # 헤더가 붙어 오히려 거부될 수 있어 None으로 바꿔 넘긴다.
    return QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY or None)
