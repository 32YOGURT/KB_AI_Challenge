"""배포용 객체 스토리지 클라이언트 (AWS S3).

app/clients/minio_client.py와 같은 3개 함수(download_to_path/presign_get/upload_bytes)를
제공한다 — app/clients/object_storage.py가 STORAGE_BACKEND에 따라 둘 중 하나를 그대로
재노출하므로, 호출부는 어느 백엔드인지 신경 쓰지 않는다.

자격증명은 boto3 기본 체인(IAM 롤 / AWS_ACCESS_KEY_ID·AWS_SECRET_ACCESS_KEY 환경변수 등)을
그대로 따른다 — 여기서 직접 읽지 않는다.
"""

from __future__ import annotations

from datetime import timedelta
from functools import lru_cache
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

from app.config import AWS_REGION, S3_BUCKET_NAME


@lru_cache
def get_client():
    return boto3.client("s3", region_name=AWS_REGION)


def download_to_path(key: str, dest: Path) -> None:
    """key로 저장된 객체를 dest 경로에 내려받는다 (부모 디렉터리는 자동 생성)."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    get_client().download_file(S3_BUCKET_NAME, key, str(dest))


def presign_get(key: str, expires: timedelta) -> str | None:
    """브라우저가 직접 PDF를 받아갈 수 있는 임시 URL을 발급한다. 객체가 없으면 None."""
    client = get_client()
    try:
        client.head_object(Bucket=S3_BUCKET_NAME, Key=key)
    except ClientError:
        return None
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": S3_BUCKET_NAME, "Key": key},
        ExpiresIn=int(expires.total_seconds()),
    )


def upload_bytes(content: bytes, key: str, content_type: str) -> None:
    """바이트를 key로 업로드한다 (크롤러가 받아온 PDF 원본 저장용)."""
    get_client().put_object(Bucket=S3_BUCKET_NAME, Key=key, Body=content, ContentType=content_type)
