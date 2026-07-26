"""다운로드한 PDF의 메타데이터(raw_title, source_page_url, saved_path 등)를
crawled_data/manifest.json에 기록한다.

product_id는 여기서 채우지 않는다 (raw_title이 products.json의 canonical id와
정확히 일치한다는 보장이 없어서, 매칭은 별도 단계에서 사람이/스크립트로 확인 후 처리).
"""

from __future__ import annotations

import json
from pathlib import Path

CRAWLED_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "crawled_data"
MANIFEST_PATH = CRAWLED_DATA_DIR / "manifest.json"


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
    source_page_url: str,
    saved_path: str,
    downloaded_at: str,
) -> None:
    entries = _load()
    entries.append(
        {
            "company": company,
            "doc_type": doc_type,
            "category": category,
            "sub_category": sub_category,
            "raw_title": raw_title,
            "source_page_url": source_page_url,
            "saved_path": saved_path,
            "downloaded_at": downloaded_at,
        }
    )
    _save(entries)
