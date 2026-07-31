"""STORAGE_BACKEND(.env)에 따라 minio_client 또는 s3_client 구현을 그대로 재노출한다.

로컬 개발은 minio(docker-compose), 배포는 s3(AWS)를 쓴다 — 호출부(app/api/documents.py,
scripts/rag/ingest.py, scripts/crawl/base.py)는 이 모듈만 보고, 실제 어느 백엔드가
붙는지는 STORAGE_BACKEND 값 하나로 갈린다.
"""

from app.config import STORAGE_BACKEND

if STORAGE_BACKEND == "s3":
    from app.clients.s3_client import download_to_path, presign_get, upload_bytes
elif STORAGE_BACKEND == "minio":
    from app.clients.minio_client import download_to_path, presign_get, upload_bytes
else:
    raise ValueError(f"알 수 없는 STORAGE_BACKEND: {STORAGE_BACKEND!r} (minio 또는 s3)")

__all__ = ["download_to_path", "presign_get", "upload_bytes"]
