"""Playwright 공통 드라이버.

config/{은행}.json (은행별 카테고리 목록) 하나하나의 항목(company, doc_type,
category, url)마다 URL 도메인에 맞는 adapter(scripts/crawl/adapters/)를 찾아
목록 페이지를 열고, adapter가 찾아낸 문서 항목마다 실제 PDF 바이트를 받아와 저장한다.

어떤 은행을 크롤링할지는 이 파일의 BANKS 리스트가 정한다 (config/ 밑에 파일이
있어도 BANKS에 없으면 안 돈다 — 특정 은행만 테스트하고 싶을 때 리스트에서 빼면 됨).

은행마다 PDF를 실제로 받아오는 방식이 다르다 (KB: 클릭 → 브라우저 다운로드 이벤트,
신한: 클릭 → AJAX 응답 안의 PDF URL을 HTTP로 GET). 그래서 어댑터는 "이 항목의 PDF
바이트를 어떻게든 가져오는" fetch(page) -> bytes만 책임지고, base.py는 그 바이트를
"MinIO에 업로드 → manifest 기록"하는 공통 흐름만 담당한다 (PDF 원본은 로컬 디스크가
아니라 MinIO 버킷에 저장되고, crawled_data/manifest.json은 메타데이터만 로컬에 둔다).

adapter가 구현해야 하는 인터페이스는 Adapter 참고.

중복 저장 방지: (1) 기본약관처럼 회사 공통인 문서는 category 대신 COMMON_DOC_STORAGE_CATEGORY
("_common/") 밑에 저장해 카테고리 페이지마다 같은 문서가 복제되는 걸 경로 단계에서 막는다.
(2) 그래도 raw_title이 상품명으로 갈라져서 내용은 같은데 제목이 다른 경우(KB/신한처럼 상품
행마다 동일 기본약관을 링크)가 남는데, 이건 content_hash 기반 dedup(crawl_entry의 seen_hashes)이
잡는다 — MinIO에 다시 올리지 않고 기존 saved_path(object key)를 재사용한다.
"""

from __future__ import annotations

import hashlib
import io
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterator, Protocol

from playwright.sync_api import Page, sync_playwright

from app.clients import minio_client
from app.config import MINIO_BUCKET_NAME

from . import manifest

CONFIG_DIR = Path(__file__).resolve().parent / "config"

DEFAULT_TIMEOUT_MS = 8000

# 크롤링할 은행 목록 (파일명은 config/{bank}.json). 순서대로 처리된다.
BANKS = ["kb", "hana", "shinhan"]


@dataclass
class ItemTrigger:
    """목록 페이지의 문서 한 건. fetch(page)를 호출하면 그 문서의 PDF 바이트를 받아와야 한다.
    받아올 수 없으면(다운로드/응답이 안 뜨는 링크였음) None을 리턴한다.

    doc_type: 어댑터가 링크 텍스트 등으로 판별한 문서 종류. 판별 못 하면 None이며,
    그 경우 manifest에도 null로 그대로 기록된다 (entry의 doc_type으로 대체하지 않음).

    product_name: 상품 고유 문서(상품설명서/특약 등)를 트리거한 행의 상품명. 회사
    공통 문서(기본약관 등, 특정 상품 행이 아니라 카테고리 전체에 걸리는 문서)는 None.
    """

    raw_title: str
    fetch: Callable[[Page], bytes | None]
    doc_type: str | None = None
    product_name: str | None = None


class Adapter(Protocol):
    """은행별 어댑터가 구현해야 하는 인터페이스."""

    def iter_item_triggers(self, page: Page) -> Iterator[ItemTrigger]:
        """목록 페이지를 순회(페이지네이션 포함)하며 문서 항목을 하나씩 yield한다."""
        ...


from .adapters import hana, kb, shinhan  # noqa: E402

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


def _object_key(company: str, category: str, raw_title: str) -> str:
    return f"{company}/{category}/{_sanitize_filename(raw_title)}.pdf"


def _upload_bytes(content: bytes, company: str, category: str, raw_title: str) -> str:
    """PDF 바이트를 MinIO에 올리고 object key를 돌려준다."""
    key = _object_key(company, category, raw_title)
    minio_client.get_client().put_object(
        MINIO_BUCKET_NAME,
        key,
        io.BytesIO(content),
        length=len(content),
        content_type="application/pdf",
    )
    return key


# 공통 문서(기본약관)를 저장할 때 category 자리에 쓰는 고정 폴더명.
COMMON_DOC_STORAGE_CATEGORY = "_common"

# 링크 텍스트가 이 목록과 정확히 일치하면, 상품 행에서 트리거됐어도 회사 공통 문서로
# 취급한다 (실제 텍스트는 은행 페이지 확인 후 채워 넣는다).
COMMON_DOC_LINK_TEXTS: set[str] = set()

COMMON_DOC_LINK_TEXTS.add("예금거래기본약관")
COMMON_DOC_LINK_TEXTS.add("적립식예금약관")
COMMON_DOC_LINK_TEXTS.add("외화예금거래기본약관")
COMMON_DOC_LINK_TEXTS.add("거치식예금약관")
COMMON_DOC_LINK_TEXTS.add("입출금이자유로운예금약관")
COMMON_DOC_LINK_TEXTS.add("전자금융거래기본약관")


def _strip_whitespace(text: str) -> str:
    return re.sub(r"\s+", "", text)

_COMMON_DOC_LINK_TEXTS_NORMALIZED = {_strip_whitespace(t) for t in COMMON_DOC_LINK_TEXTS}


def resolve_common_doc(
    doc_type: str | None, link_text: str, product_name: str | None
) -> tuple[str | None, str | None]:
    if _strip_whitespace(link_text) in _COMMON_DOC_LINK_TEXTS_NORMALIZED:
        return "기본약관", None
    return doc_type, product_name


def crawl_entry(entry: dict, page: Page, seen_hashes: dict[str, str]) -> None:
    """config/{은행}.json의 한 항목(company/doc_type/category/url/adapter)을 처리한다.

    seen_hashes: content sha256 -> 그 내용으로 이미 업로드된 MinIO object key. run() 전체에서
    하나를 공유해서, 이 실행 중 어디서든 내용이 같은 파일을 다시 받으면(예: KB/신한처럼
    상품 행마다 동일한 기본약관을 링크하는 경우) MinIO에 다시 올리지 않고 기존 object를
    가리키게 한다"""
    adapter = _adapter_for(entry["adapter"])
    page.goto(entry["url"])

    for trigger in adapter.iter_item_triggers(page):
        content = trigger.fetch(page)
        if content is None:
            print(f"[skip] PDF를 못 받아옴: {trigger.raw_title}")
            continue

        content_hash = hashlib.sha256(content).hexdigest()
        existing_path = seen_hashes.get(content_hash)
        if existing_path is not None:
            saved_path = existing_path
            print(f"[dedup] 동일 파일 재사용: {trigger.raw_title} -> {existing_path}")
        else:
            storage_category = (
                COMMON_DOC_STORAGE_CATEGORY if trigger.doc_type == "기본약관" else entry["category"]
            )
            saved_path = _upload_bytes(content, entry["company"], storage_category, trigger.raw_title)
            seen_hashes[content_hash] = saved_path

        # product_id: product_name이 없으면(회사 공통 문서로 판별됨) None, 있으면 채운다.
        if trigger.product_name is None:
            product_id = None
        else:
            product_id = manifest.generate_product_id(entry["company"], trigger.product_name)

        manifest.append_entry(
            company=entry["company"],
            doc_type=trigger.doc_type,
            category=entry["category"],
            sub_category=entry.get("sub_category"),
            raw_title=trigger.raw_title,
            product_name=trigger.product_name,
            product_id=product_id,
            content_hash=content_hash,
            source_page_url=page.url,
            saved_path=saved_path,
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
    # manifest에 이미 content_hash가 기록된 이전 실행 결과로 시드한다 — 재실행 시에도
    # 이전에 받은 파일과 내용이 같으면 다시 저장하지 않는다.
    seen_hashes = manifest.existing_hash_index()
    with sync_playwright() as p:
        for entry in entries:
            # entry(카테고리)마다 브라우저 자체를 새로 띄운다. page만 새로 만드는 걸로는
            # 부족했음 — 신한처럼 팝업을 수십~수백 번 열고 닫는 경우 브라우저 프로세스
            # 자체에 뭔가 누적되다가 몇 카테고리 뒤에 죽는 문제가 있었다 (실제로 마지막
            # 카테고리만 따로 돌리면 문제없이 성공하는 걸로 확인됨 — 누적 문제가 맞음).
            # 카테고리 수가 몇 개 안 되니 매번 새로 띄워도 비용은 크지 않다.
            try:
                browser = p.chromium.launch(headless=headless)
            except Exception as e:
                # 브라우저 실행 자체가 실패한 경우(직전 entry의 Page crashed로 드라이버가
                # 불안정해졌을 때 등)도 여기서 잡아서 이 entry만 건너뛴다 — 이전엔 이 줄이
                # try 밖에 있어서 전체 스크립트가 죽었었다.
                print(f"[skip entry] {entry.get('company')}/{entry.get('sub_category')}: 브라우저 실행 실패: {e}")
                continue
            page = browser.new_page()
            try:
                crawl_entry(entry, page, seen_hashes)
            except Exception as e:
                # 카테고리 하나의 구조 문제(selector 불일치 등)로 전체가 멈추지 않게,
                # 여기서 잡고 다음 entry로 넘어간다. 이미 처리된 항목의 manifest 기록은 남는다.
                print(f"[skip entry] {entry.get('company')}/{entry.get('sub_category')}: {e}")
            finally:
                try:
                    browser.close()
                except Exception:
                    pass
