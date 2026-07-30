"""크롤링한 PDF 원본을 저장하는 MinIO(S3 호환) 클라이언트.

docker-compose.yml로 로컬 기동 시 기본값 사용 (http://localhost:9000).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit

from minio import Minio

from app.config import MINIO_BUCKET_NAME, MINIO_ENDPOINT_URL, MINIO_ROOT_PASSWORD, MINIO_ROOT_USER


@lru_cache
def get_client() -> Minio:
    endpoint = urlsplit(MINIO_ENDPOINT_URL)
    client = Minio(
        endpoint.netloc,
        access_key=MINIO_ROOT_USER,
        secret_key=MINIO_ROOT_PASSWORD,
        secure=endpoint.scheme == "https",
    )
    if not client.bucket_exists(MINIO_BUCKET_NAME):
        client.make_bucket(MINIO_BUCKET_NAME)
    return client


def download_to_path(key: str, dest: Path) -> None:
    """key로 저장된 객체를 dest 경로에 내려받는다 (부모 디렉터리는 자동 생성)."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    get_client().fget_object(MINIO_BUCKET_NAME, key, str(dest))
