"""다운로드한 PDF의 메타데이터(raw_title, product_name, product_id, source_page_url,
saved_path 등)를 crawled_data/manifest.json에 기록한다.
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


def append_entry(
    *,
    company: str,
    doc_type: str | None,
    category: str,
    sub_category: str | None,
    raw_title: str,
    product_name: str | None,
    product_id: str | None,
    source_page_url: str,
    saved_path: str,  # CRAWLED_DATA_DIR 기준 상대경로(POSIX 슬래시). 절대경로 아님.
    downloaded_at: str,
) -> None:
    """saved_path는 company+category+raw_title로 결정적으로 정해지므로, 같은 문서를
    재크롤링하면 항상 같은 saved_path가 나온다. 이를 키로 삼아 기존 엔트리는 덮어쓰고
    새 문서만 추가한다 — 크롤러를 여러 번 돌려도 manifest가 중복으로 불어나지 않게 한다."""
    entries = _load()
    new_entry = {
        "company": company,
        "doc_type": doc_type,
        "category": category,
        "sub_category": sub_category,
        "raw_title": raw_title,
        "product_name": product_name,
        "product_id": product_id,
        "source_page_url": source_page_url,
        "saved_path": saved_path,
        "downloaded_at": downloaded_at,
    }
    for i, entry in enumerate(entries):
        if entry["saved_path"] == saved_path:
            entries[i] = new_entry
            break
    else:
        entries.append(new_entry)
    _save(entries)
