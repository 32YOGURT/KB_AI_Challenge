"""다운로드한 PDF의 메타데이터(raw_title, product_name, product_id, content_hash,
source_page_url, saved_path 등)를 crawled_data/manifest.json에 기록한다.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

CRAWLED_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "crawled_data"
MANIFEST_PATH = CRAWLED_DATA_DIR / "manifest.json"


def generate_product_id(company: str, product_name: str) -> str:
    """company+product_name으로 결정적 고유 id를 만든다 (같은 상품이면 항상 같은 id).
    가독성보다 유일성만 보장하면 되므로 해시 기반으로 짧게 자른다."""
    digest = hashlib.sha1(f"{company}::{product_name}".encode("utf-8")).hexdigest()
    return digest[:12]


def _load() -> list[dict]:
    if not MANIFEST_PATH.exists():
        return []
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _save(entries: list[dict]) -> None:
    CRAWLED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")


def existing_hash_index() -> dict[str, str]:
    """manifest에 이미 기록된 content_hash -> saved_path 매핑을 돌려준다.

    크롤링 시작 시 이걸로 dedup 인덱스를 시드하면, 이전 실행에서 받은 파일과 내용이
    같은 문서를 이번 실행에서 다시 받더라도 디스크에 중복 저장하지 않는다. content_hash가
    없는(이 필드가 생기기 전에 기록된) 엔트리는 그냥 건너뛴다."""
    return {
        entry["content_hash"]: entry["saved_path"]
        for entry in _load()
        if entry.get("content_hash")
    }


def append_entry(
    *,
    company: str,
    doc_type: str | None,
    category: str,
    sub_category: str | None,
    raw_title: str,
    product_name: str | None,
    product_id: str | None,
    content_hash: str,
    source_page_url: str,
    saved_path: str,  # MinIO object key ("{company}/{category}/{title}.pdf"). 로컬 경로 아님.
    downloaded_at: str,
) -> None:
    """(company, category, raw_title)로 문서 한 건을 식별한다. 같은 문서를 재크롤링하면
    이 조합이 그대로 나오므로, 기존 엔트리는 덮어쓰고 새 문서만 추가한다 — 크롤러를 여러
    번 돌려도 manifest가 중복으로 불어나지 않게 한다.

    saved_path를 키로 쓰지 않는 이유: content_hash가 같은 문서(예: 상품 행마다 동일한
    기본약관을 링크하는 KB/신한)는 실제 파일을 한 번만 저장하고 여러 엔트리가 같은
    saved_path를 공유하기 때문 — saved_path로 매칭하면 서로 다른 상품의 엔트리를
    잘못 덮어쓰게 된다."""
    entries = _load()
    new_entry = {
        "company": company,
        "doc_type": doc_type,
        "category": category,
        "sub_category": sub_category,
        "raw_title": raw_title,
        "product_name": product_name,
        "product_id": product_id,
        "content_hash": content_hash,
        "source_page_url": source_page_url,
        "saved_path": saved_path,
        "downloaded_at": downloaded_at,
    }
    identity = (company, category, raw_title)
    for i, entry in enumerate(entries):
        if (entry["company"], entry["category"], entry["raw_title"]) == identity:
            entries[i] = new_entry
            break
    else:
        entries.append(new_entry)
    _save(entries)
