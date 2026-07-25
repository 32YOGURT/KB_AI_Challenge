"""Playwright 공통 드라이버.

config.json의 항목(company, doc_type, category, url)마다 URL 도메인에 맞는
adapter(scripts/crawl/adapters/)를 찾아 목록 페이지를 열고, adapter가 찾아낸
문서 항목을 하나씩 클릭해 다운로드 이벤트를 캡처/저장한다.

은행별 목록 HTML 구조나 다운로드 트리거 방식(JS onclick 등)은 adapter가 책임지고,
base.py는 "다운로드 캡처 → 파일 저장 → manifest 기록" 공통 흐름만 담당한다.

adapter가 구현해야 하는 인터페이스는 Adapter 참고.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterator, Protocol

from playwright.sync_api import Download, Page, TimeoutError as PlaywrightTimeoutError, sync_playwright

from . import manifest


@dataclass
class ItemTrigger:
    """목록 페이지의 문서 한 건. click(page)를 호출하면 다운로드가 트리거되어야 한다.

    doc_type: 어댑터가 링크 텍스트 등으로 판별한 문서 종류. 판별 못 하면 None이며,
    그 경우 manifest에도 null로 그대로 기록된다 (entry의 doc_type으로 대체하지 않음).
    """

    raw_title: str
    click: Callable[[Page], None]
    doc_type: str | None = None


class Adapter(Protocol):
    """은행별 어댑터가 구현해야 하는 인터페이스."""

    def iter_item_triggers(self, page: Page) -> Iterator[ItemTrigger]:
        """목록 페이지를 순회(페이지네이션 포함)하며 문서 항목을 하나씩 yield한다."""
        ...


# adapters는 ItemTrigger/Adapter를 정의한 뒤에 import해야 함 (adapters/*.py가
# `from ..base import ItemTrigger`로 참조하므로, 먼저 import하면 순환 참조로 깨짐).
from .adapters import hana, kb, shinhan  # noqa: E402

# config.json의 "adapter" 필드 값 -> adapter 모듈
ADAPTERS = {
    "kb": kb,
    "hana": hana,
    "shinhan": shinhan,
}


def _adapter_for(name: str) -> Adapter:
    try:
        return ADAPTERS[name]
    except KeyError:
        raise ValueError(f"등록되지 않은 adapter: {name!r} (사용 가능: {list(ADAPTERS)})") from None


def _sanitize_filename(title: str) -> str:
    return re.sub(r'[\\/:*?"<>|]', "_", title).strip()


def _save_download(download: Download, company: str, category: str, raw_title: str) -> Path:
    out_dir = manifest.CRAWLED_DATA_DIR / company / category
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{_sanitize_filename(raw_title)}.pdf"
    download.save_as(out_path)
    return out_path


def crawl_entry(entry: dict, page: Page) -> None:
    """config.json의 한 항목(company/doc_type/category/url/adapter)을 처리한다."""
    adapter = _adapter_for(entry["adapter"])
    page.goto(entry["url"])

    for trigger in adapter.iter_item_triggers(page):
        try:
            with page.expect_download(timeout=5000) as download_info:
                trigger.click(page)
        except PlaywrightTimeoutError:
            # 클릭했는데 다운로드가 안 뜬 경우 (문서 링크가 아니었거나 다른 동작을 하는
            # 링크였음). 전체 크롤링을 막지 않고 그냥 이 항목만 건너뛴다.
            print(f"[skip] 다운로드 발생 안 함: {trigger.raw_title}")
            continue

        saved_path = _save_download(
            download_info.value, entry["company"], entry["category"], trigger.raw_title
        )
        # doc_type: 어댑터가 판별 못 하면 None(=null)으로 그대로 저장한다.
        # entry["doc_type"]로 대체하지 않음 — kb처럼 한 행에 여러 문서종류가 섞인 경우
        # config 값 자체가 의미 없는 placeholder("TODO")라 fallback으로 쓰면 안 됨.
        manifest.append_entry(
            company=entry["company"],
            doc_type=trigger.doc_type,
            category=entry["category"],
            raw_title=trigger.raw_title,
            source_page_url=page.url,
            saved_path=str(saved_path),
            downloaded_at=datetime.now(timezone.utc).isoformat(),
        )


def run(config_path: Path, headless: bool = True) -> None:
    entries = json.loads(config_path.read_text(encoding="utf-8"))
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()
        for entry in entries:
            crawl_entry(entry, page)
        browser.close()
