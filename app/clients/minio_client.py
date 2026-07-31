"""크롤링한 PDF 원본을 저장하는 MinIO(S3 호환) 클라이언트.

docker-compose.yml로 로컬 기동 시 기본값 사용 (http://localhost:9000).
"""

from __future__ import annotations

import io
from datetime import timedelta
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit

from minio import Minio
from minio.error import S3Error

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


def upload_bytes(content: bytes, key: str, content_type: str) -> None:
    """바이트를 key로 업로드한다 (크롤러가 받아온 PDF 원본 저장용)."""
    get_client().put_object(
        MINIO_BUCKET_NAME, key, io.BytesIO(content), length=len(content), content_type=content_type
    )


def presign_get(key: str, expires: timedelta) -> str | None:
    """브라우저가 직접 PDF를 받아갈 수 있는 임시 URL을 발급한다. 객체가 없으면 None.

    presigned_get_object는 객체 존재를 확인하지 않아서, 없는 key에도 나중에 404를 뱉는
    URL을 만들어준다 — 호출부가 바로 404를 줄 수 있게 stat_object로 먼저 확인한다.
    """
    client = get_client()
    try:
        client.stat_object(MINIO_BUCKET_NAME, key)
    except S3Error:
        return None
    return client.presigned_get_object(MINIO_BUCKET_NAME, key, expires=expires)
