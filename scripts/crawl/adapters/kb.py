"""KB국민은행 상품설명서/약관 자료실 어댑터.

목록은 테이블 형태이고, 한 행(row)이 상품 하나다. 행 안에 문서 종류별 링크
(예금거래기본약관/적립식예금약관/특약/상품설명서 등)가 여러 개 들어있어서,
이 어댑터는 (상품, 문서링크) 조합마다 ItemTrigger를 하나씩 yield하고
문서 종류는 config의 doc_type 대신 링크 텍스트로 판별해 오버라이드한다.

각 링크는 href="#none" + 클라이언트 JS(onclick)로 처리된다.

참고 페이지: https://obank.kbstar.com/quics?page=C022182 (적립식예금)
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from ..base import DEFAULT_TIMEOUT_MS, ItemTrigger

# 링크 텍스트에 아래 키워드가 포함되어 있으면 해당 doc_type으로 판별한다.
# 예금거래기본약관/적립식예금약관처럼 공통 문서는 텍스트가 고정이지만,
# 특약/상품설명서는 "KB내맘대로적금 특약"처럼 상품명이 앞에 붙어서 나오므로
# 완전일치가 아니라 포함 여부로 봐야 한다.
# 매핑 키워드가 하나도 없는 링크(예: "공시자료변경")도 일단 클릭은 시도하되, doc_type은 None.
DOC_TYPE_MAP = {
    "특약": "특약",
    "상품설명서": "상품설명서",
    # "적립식예금기본약관"/"입출금이자유로운예금약관"처럼 실제 링크 텍스트는 종류가 다양해서
    # 개별 나열 대신 "약관"을 마지막 catch-all로 둔다 (하나은행 어댑터와 동일 패턴).
    "약관": "기본약관",
}


def _resolve_doc_type(link_text: str) -> str | None:
    for keyword, doc_type in DOC_TYPE_MAP.items():
        if keyword in link_text:
            return doc_type
    return None

# 카테고리 페이지마다 목록 바로 위 컨테이너 id(예: #b054049)가 달라서, 그 대신
# 고정된 div#CP 밑에서 div만 세었을 때 3번째 자식으로 잡는다 (구조는 페이지마다 공통).
ROW_SELECTOR = "div.contentWrap > div#CP > div:nth-of-type(3) > div.n_pcontZn > form > div.n_prodList > table.tType01 > tbody > tr"
# 상품명은 클릭 대상이 아니라 텍스트만 읽으면 되므로 a로 좁히지 않는다.
# (외화 계열처럼 th.th01 안에 <a> 없이 텍스트만 있는 페이지도 있음)
PRODUCT_NAME_SELECTOR = "th.th01"
DOC_LINK_SELECTOR = "td.tLeft a"
# 페이지 번호가 <a>가 아니라 폼별 제출 버튼으로 되어 있음:
#   <form onsubmit="return goPage(N);">
#     <input type="hidden" name="NEXT_TAG_PAGE" value="N">
#     <input type="submit" value="N" title="N페이지">
#   </form>
# 번호는 텍스트가 아니라 value 속성에 있어서 inner_text() 대신 get_attribute("value")로 비교해야 함.
PAGE_NUMBER_SELECTOR = "div.paging input[type=submit]"


def _fetch(page: Page, link_locator) -> bytes | None:
    """클릭하면 브라우저 다운로드 이벤트가 뜨는 방식. 안 뜨면(문서 링크가 아니었음) None."""
    try:
        with page.expect_download(timeout=DEFAULT_TIMEOUT_MS) as download_info:
            link_locator.click()
    except PlaywrightTimeoutError:
        return None
    download = download_info.value
    return Path(download.path()).read_bytes()


def _find_page_link(page: Page, page_number: int):
    """페이지 번호 제출 버튼들 중 value가 page_number와 일치하는 것을 찾는다.
    페이지네이션 자체가 없는 페이지(외화 계열 등, 상품 수가 적어 페이지가 하나뿐인 경우)에서는
    PAGE_NUMBER_SELECTOR가 아무것도 안 잡히므로 자연히 None."""
    buttons = page.locator(PAGE_NUMBER_SELECTOR).all()
    if not buttons:
        return None
    for button in buttons:
        if button.get_attribute("value") == str(page_number):
            return button
    return None


def iter_item_triggers(page: Page) -> Iterator[ItemTrigger]:
    current_page = 1
    while True:
        rows = page.locator(ROW_SELECTOR).all()
        for row in rows:
            try:
                product_name = row.locator(PRODUCT_NAME_SELECTOR).inner_text(timeout=DEFAULT_TIMEOUT_MS).strip()
            except PlaywrightTimeoutError:
                # 상품명 칸이 없는 행(구분선/안내 행 등 데이터가 아닌 행)은 건너뛴다.
                continue

            for link in row.locator(DOC_LINK_SELECTOR).all():
                link_text = link.inner_text().strip()
                doc_type = _resolve_doc_type(link_text)

                def fetch(p: Page, link=link) -> bytes | None:
                    return _fetch(p, link)

                yield ItemTrigger(
                    raw_title=f"{product_name}_{link_text}",
                    fetch=fetch,
                    doc_type=doc_type,
                    product_name=product_name,
                )

        next_page_link = _find_page_link(page, current_page + 1)
        if next_page_link is None:
            break
        next_page_link.click()
        page.wait_for_load_state("networkidle")
        current_page += 1
