"""Playwright 공통 드라이버.

config/{은행}.json (은행별 카테고리 목록) 하나하나의 항목(company, doc_type,
category, url)마다 URL 도메인에 맞는 adapter(scripts/crawl/adapters/)를 찾아
목록 페이지를 열고, adapter가 찾아낸 문서 항목마다 실제 PDF 바이트를 받아와 저장한다.

어떤 은행을 크롤링할지는 이 파일의 BANKS 리스트가 정한다 (config/ 밑에 파일이
있어도 BANKS에 없으면 안 돈다 — 특정 은행만 테스트하고 싶을 때 리스트에서 빼면 됨).

은행마다 PDF를 실제로 받아오는 방식이 다르다 (KB: 클릭 → 브라우저 다운로드 이벤트,
신한: 클릭 → AJAX 응답 안의 PDF URL을 HTTP로 GET). 그래서 어댑터는 "이 항목의 PDF
바이트를 어떻게든 가져오는" fetch(page) -> bytes만 책임지고, base.py는 그 바이트를
"파일로 저장 → manifest 기록"하는 공통 흐름만 담당한다.

adapter가 구현해야 하는 인터페이스는 Adapter 참고.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterator, Protocol

from playwright.sync_api import Page, sync_playwright

from . import manifest

CONFIG_DIR = Path(__file__).resolve().parent / "config"

# 크롤링할 은행 목록 (파일명은 config/{bank}.json). 순서대로 처리된다.
BANKS = ["kb", "shinhan", "hana"]


@dataclass
class ItemTrigger:
    """목록 페이지의 문서 한 건. fetch(page)를 호출하면 그 문서의 PDF 바이트를 받아와야 한다.
    받아올 수 없으면(다운로드/응답이 안 뜨는 링크였음) None을 리턴한다.

    doc_type: 어댑터가 링크 텍스트 등으로 판별한 문서 종류. 판별 못 하면 None이며,
    그 경우 manifest에도 null로 그대로 기록된다 (entry의 doc_type으로 대체하지 않음).
    """

    raw_title: str
    fetch: Callable[[Page], bytes | None]
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


def _save_bytes(content: bytes, company: str, category: str, raw_title: str) -> Path:
    out_dir = manifest.CRAWLED_DATA_DIR / company / category
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{_sanitize_filename(raw_title)}.pdf"
    out_path.write_bytes(content)
    return out_path


def crawl_entry(entry: dict, page: Page) -> None:
    """config/{은행}.json의 한 항목(company/doc_type/category/url/adapter)을 처리한다."""
    adapter = _adapter_for(entry["adapter"])
    page.goto(entry["url"])

    for trigger in adapter.iter_item_triggers(page):
        content = trigger.fetch(page)
        if content is None:
            # 어댑터가 PDF를 못 받아온 경우 (문서 링크가 아니었거나 다른 동작을 하는
            # 링크였음). 전체 크롤링을 막지 않고 그냥 이 항목만 건너뛴다.
            print(f"[skip] PDF를 못 받아옴: {trigger.raw_title}")
            continue

        saved_path = _save_bytes(
            content, entry["company"], entry["category"], trigger.raw_title
        )
        # doc_type: 어댑터가 판별 못 하면 None(=null)으로 그대로 저장한다.
        # entry["doc_type"]로 대체하지 않음 — kb처럼 한 행에 여러 문서종류가 섞인 경우
        # config 값 자체가 의미 없는 placeholder("TODO")라 fallback으로 쓰면 안 됨.
        manifest.append_entry(
            company=entry["company"],
            doc_type=trigger.doc_type,
            category=entry["category"],
            sub_category=entry.get("sub_category"),
            raw_title=trigger.raw_title,
            source_page_url=page.url,
            saved_path=str(saved_path),
            downloaded_at=datetime.now(timezone.utc).isoformat(),
        )


def _load_entries() -> list[dict]:
    entries: list[dict] = []
    for bank in BANKS:
        config_path = CONFIG_DIR / f"{bank}.json"
        entries.extend(json.loads(config_path.read_text(encoding="utf-8")))
    return entries


def run(headless: bool = True) -> None:
    entries = _load_entries()
    with sync_playwright() as p:
        for entry in entries:
            # entry(카테고리)마다 브라우저 자체를 새로 띄운다. page만 새로 만드는 걸로는
            # 부족했음 — 신한처럼 팝업을 수십~수백 번 열고 닫는 경우 브라우저 프로세스
            # 자체에 뭔가 누적되다가 몇 카테고리 뒤에 죽는 문제가 있었다 (실제로 마지막
            # 카테고리만 따로 돌리면 문제없이 성공하는 걸로 확인됨 — 누적 문제가 맞음).
            # 카테고리 수가 몇 개 안 되니 매번 새로 띄워도 비용은 크지 않다.
            browser = p.chromium.launch(headless=headless)
            page = browser.new_page()
            try:
                crawl_entry(entry, page)
            except Exception as e:
                # 카테고리 하나의 구조 문제(selector 불일치 등)로 전체가 멈추지 않게,
                # 여기서 잡고 다음 entry로 넘어간다. 이미 처리된 항목의 manifest 기록은 남는다.
                print(f"[skip entry] {entry.get('company')}/{entry.get('sub_category')}: {e}")
            finally:
                try:
                    browser.close()
                except Exception:
                    pass
