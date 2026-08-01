"""로컬 MinIO 버킷의 객체를 배포용 AWS S3 버킷으로 그대로 복사한다.

배포 환경(STORAGE_BACKEND=s3)에서 PDF 뷰어가 동작하려면, 크롤러가 로컬 MinIO에 쌓아둔
원본 PDF가 S3에도 같은 object key로 올라가 있어야 한다 — Qdrant에 색인된 조항의
source_key가 그 key를 그대로 가리키기 때문이다.

app/clients/object_storage.py(디스패처)를 쓰지 않고 두 클라이언트를 직접 import한다 —
디스패처는 STORAGE_BACKEND 하나만 골라 노출하는데, 여기선 양쪽이 동시에 필요하다.

이미 올라간 객체는 건너뛰므로 중간에 끊겨도 다시 실행하면 이어서 진행된다.

사용법:
    # 무엇이 올라갈지만 확인 (실제 업로드 없음)
    python scripts/storage/migrate_minio_to_s3.py --dry-run

    # 실제 업로드
    python scripts/storage/migrate_minio_to_s3.py

    # 크기가 다른 객체는 이미 있어도 다시 올린다
    python scripts/storage/migrate_minio_to_s3.py --overwrite

선행 조건:
    - 로컬 MinIO가 떠 있고 .env의 MINIO_* 설정이 맞을 것
    - .env에 S3_BUCKET_NAME / AWS_REGION 과 쓰기 권한이 있는 자격증명(s3:PutObject)이 있을 것
      (배포 EC2 롤과 달리 여기선 업로드를 하므로 쓰기 권한이 필요하다)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.stdout.reconfigure(encoding="utf-8")

from botocore.exceptions import ClientError  # noqa: E402

from app.clients import minio_client, s3_client  # noqa: E402
from app.config import AWS_REGION, MINIO_BUCKET_NAME, S3_BUCKET_NAME  # noqa: E402

DEFAULT_CONTENT_TYPE = "application/pdf"


def _s3_object_size(key: str) -> int | None:
    """S3에 있으면 크기를, 없으면 None을 돌려준다."""
    try:
        head = s3_client.get_client().head_object(Bucket=S3_BUCKET_NAME, Key=key)
    except ClientError:
        return None
    return head["ContentLength"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="업로드 없이 대상만 출력")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="이미 S3에 있어도 크기가 다르면 다시 올린다 (기본은 존재하면 무조건 건너뜀)",
    )
    args = parser.parse_args()

    if not S3_BUCKET_NAME:
        parser.error("S3_BUCKET_NAME이 비어 있다 — .env를 확인할 것")

    source = minio_client.get_client()
    objects = sorted(
        source.list_objects(MINIO_BUCKET_NAME, recursive=True), key=lambda o: o.object_name
    )
    print(f"MinIO({MINIO_BUCKET_NAME}) 객체 {len(objects)}개 -> S3({S3_BUCKET_NAME}, {AWS_REGION})\n")

    uploaded = skipped = failed = 0
    uploaded_bytes = 0

    for i, obj in enumerate(objects, start=1):
        key = obj.object_name
        tag = f"[{i}/{len(objects)}] {key}"

        existing_size = _s3_object_size(key)
        if existing_size is not None and not (args.overwrite and existing_size != obj.size):
            skipped += 1
            continue

        if args.dry_run:
            reason = "재업로드" if existing_size is not None else "신규"
            print(f"{tag} -> {reason} ({obj.size:,} bytes)")
            uploaded += 1
            continue

        # get_object는 스트림을 돌려주므로 반드시 닫아야 커넥션 풀이 마르지 않는다.
        response = None
        try:
            response = source.get_object(MINIO_BUCKET_NAME, key)
            content = response.read()
        except Exception as e:  # noqa: BLE001 - 개별 객체 실패가 전체를 막지 않게 한다
            print(f"{tag} -> 다운로드 실패: {e!r}")
            failed += 1
            continue
        finally:
            if response is not None:
                response.close()
                response.release_conn()

        content_type = getattr(obj, "content_type", None) or DEFAULT_CONTENT_TYPE
        try:
            s3_client.upload_bytes(content, key, content_type)
        except Exception as e:  # noqa: BLE001
            print(f"{tag} -> 업로드 실패: {e!r}")
            failed += 1
            continue

        uploaded += 1
        uploaded_bytes += len(content)
        print(f"{tag} -> 완료 ({len(content):,} bytes)")

    verb = "업로드 예정" if args.dry_run else "업로드"
    print(
        f"\n{verb} {uploaded}개 ({uploaded_bytes / 1024 / 1024:.1f} MB), "
        f"이미 존재해서 건너뜀 {skipped}개, 실패 {failed}개"
    )
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
