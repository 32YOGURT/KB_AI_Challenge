"""하나은행 상품설명서/약관 자료실 어댑터.

목록은 평범한 서버 렌더링 테이블(table.tblBoard)이고, 한 행이 상품 하나다.
행 안의 "상품설명서"/"약관" 링크는 onclick="window.open('URL', 'window', ...)"로
새 창(진짜 새 탭, 오버레이 아님)을 여는데, 그 창 자체가 실제 PDF가 아니라
시행일별 PDF 목록을 보여주는 뷰어 페이지다. 이 어댑터는 그 창을 실제로 열지 않고,
onclick에서 URL만 뽑아 HTTP GET으로 직접 받은 뒤(HTML), 그 안 <iframe src="...pdf">
(항상 가장 최신 시행일 버전)를 정규식으로 추출해 다시 HTTP GET으로 PDF 바이트를 받는다.

그리고 KB/신한과 달리, 상품별 문서 말고도 카테고리 페이지 하단에 공통 약관
("기본약관" h4 + ul.listFile) 섹션이 있다 — 예: 예금거래기본약관, 거치식예금약관,
비과세종합저축 특약 등. 이건 상품 하나에 속한 게 아니라 카테고리 전체 공통이라
페이지네이션 매 페이지에 뜨더라도 첫 페이지에서만 한 번 수집한다.

참고 페이지: https://www.kebhana.com/cont/mall/mall09/mall0902/mall090202/index.jsp (정기예금)
"""

from __future__ import annotations

import re
from typing import Iterator
from urllib.parse import urljoin

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from ..base import DEFAULT_TIMEOUT_MS, ItemTrigger

# 링크 텍스트에 포함된 키워드로 doc_type을 판별한다 (KB/신한과 동일한 이유: 상품명이나
# 접두어가 붙어서 나오는 경우가 있어 완전일치 대신 포함 여부로 본다).
# "약관"만 있으면 예금거래기본약관/적립식예금약관/거치식예금약관/외화예금거래기본약관/
# 입출금이자유로운예금약관 등 이름이 다른 공통약관들이 전부 걸린다 (전부 기본약관으로 취급).
DOC_TYPE_MAP = {
    "특약": "특약",
    "상품설명서": "상품설명서",
    "약관": "기본약관",
}


def _resolve_doc_type(link_text: str) -> str | None:
    for keyword, doc_type in DOC_TYPE_MAP.items():
        if keyword in link_text:
            return doc_type
    return None


def _normalize(text: str) -> str:
    return " ".join(text.split())


ROW_SELECTOR = "table.tblBoard > tbody > tr"
PRODUCT_NAME_SELECTOR = "td"  # 첫 번째 td가 상품명 (링크로 감싸진 경우/아닌 경우 둘 다 있음)
DOC_LINK_SELECTOR = "td.btnDb a.btnTxt.pdf"
# 카테고리 페이지 하단 공통약관 섹션. "기본약관" h4 다음에 오는 목록.
COMMON_TERMS_LINK_SELECTOR = "ul.listFile a.btnTxt.pdf"
# 페이지네이션은 진짜 <a href>라 클릭하면 일반 페이지 이동이 된다 (SPA 아님).
# 맨앞/이전/다음/끝 버튼도 같은 태그라 class로 걸러내고 번호만 남긴다.
PAGE_LINK_SELECTOR = "div.paging a"
PAGE_LINK_SKIP_CLASSES = ("first", "prev", "next", "end")

_ONCLICK_URL_RE = re.compile(r"window\.open\('([^']+)'")
_IFRAME_PDF_RE = re.compile(r'<iframe[^>]+src="([^"]+\.pdf)"')


def _extract_popup_url(onclick: str, base_url: str) -> str | None:
    match = _ONCLICK_URL_RE.search(onclick)
    if not match:
        return None
    return urljoin(base_url, match.group(1))


def _fetch(page: Page, popup_url: str) -> bytes | None:
    """popup_url(뷰어 페이지)을 HTTP GET으로 받아 그 안의 <iframe> PDF URL을 추출한 뒤,
    그 PDF를 다시 HTTP GET으로 받는다. 실제 창을 열지 않는다 (KB/신한과 다른 방식이지만
    둘 다 결국 'UI 상호작용 대신 그 결과물이 있는 URL을 직접 받는다'는 같은 전략)."""
    try:
        resp = page.context.request.get(popup_url, timeout=DEFAULT_TIMEOUT_MS)
    except PlaywrightTimeoutError:
        return None
    if not resp.ok:
        return None

    match = _IFRAME_PDF_RE.search(resp.text())
    if not match:
        return None
    pdf_url = match.group(1)

    try:
        pdf_resp = page.context.request.get(pdf_url, timeout=DEFAULT_TIMEOUT_MS)
    except PlaywrightTimeoutError:
        return None
    if not pdf_resp.ok:
        return None
    return pdf_resp.body()


def _find_page_link(page: Page, page_number: int):
    for link in page.locator(PAGE_LINK_SELECTOR).all():
        cls = link.get_attribute("class") or ""
        if any(skip in cls for skip in PAGE_LINK_SKIP_CLASSES):
            continue
        if link.inner_text().strip() == str(page_number):
            return link
    return None


def _iter_row_triggers(page: Page) -> Iterator[ItemTrigger]:
    for row in page.locator(ROW_SELECTOR).all():
        try:
            product_name = _normalize(row.locator(PRODUCT_NAME_SELECTOR).first.inner_text(timeout=DEFAULT_TIMEOUT_MS))
        except PlaywrightTimeoutError:
            continue

        for link in row.locator(DOC_LINK_SELECTOR).all():
            try:
                link_text = _normalize(link.inner_text(timeout=DEFAULT_TIMEOUT_MS))
            except PlaywrightTimeoutError:
                continue
            onclick = link.get_attribute("onclick") or ""
            popup_url = _extract_popup_url(onclick, page.url)
            if popup_url is None:
                continue
            doc_type = _resolve_doc_type(link_text)

            def fetch(p: Page, popup_url=popup_url) -> bytes | None:
                return _fetch(p, popup_url)

            yield ItemTrigger(
                raw_title=f"{product_name}_{link_text}",
                fetch=fetch,
                doc_type=doc_type,
                product_name=product_name,
            )


def _iter_common_terms_triggers(page: Page) -> Iterator[ItemTrigger]:
    for link in page.locator(COMMON_TERMS_LINK_SELECTOR).all():
        try:
            link_text = _normalize(link.inner_text(timeout=DEFAULT_TIMEOUT_MS))
        except PlaywrightTimeoutError:
            continue
        onclick = link.get_attribute("onclick") or ""
        popup_url = _extract_popup_url(onclick, page.url)
        if popup_url is None:
            continue
        doc_type = _resolve_doc_type(link_text)

        def fetch(p: Page, popup_url=popup_url) -> bytes | None:
            return _fetch(p, popup_url)

        yield ItemTrigger(raw_title=link_text, fetch=fetch, doc_type=doc_type)


def iter_item_triggers(page: Page) -> Iterator[ItemTrigger]:
    current_page = 1
    while True:
        yield from _iter_row_triggers(page)

        # 공통약관 섹션은 카테고리당 한 번만 (페이지마다 동일하게 뜨는 걸로 보여서).
        if current_page == 1:
            yield from _iter_common_terms_triggers(page)

        next_page_link = _find_page_link(page, current_page + 1)
        if next_page_link is None:
            break
        next_page_link.click()
        page.wait_for_load_state("networkidle")
        current_page += 1
