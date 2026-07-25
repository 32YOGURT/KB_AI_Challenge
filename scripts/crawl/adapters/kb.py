"""KB국민은행 상품설명서/약관 자료실 어댑터.

목록은 테이블 형태이고, 한 행(row)이 상품 하나다. 행 안에 문서 종류별 링크
(예금거래기본약관/적립식예금약관/특약/상품설명서 등)가 여러 개 들어있어서,
이 어댑터는 (상품, 문서링크) 조합마다 ItemTrigger를 하나씩 yield하고
문서 종류는 config의 doc_type 대신 링크 텍스트로 판별해 오버라이드한다.

각 링크는 href="#none" + 클라이언트 JS(onclick)로 처리되는 것으로 보이며,
실제 onclick 핸들러/selector는 아직 확인 전. 아래 selector들은 전부 TODO.

참고 페이지: https://obank.kbstar.com/quics?page=C022182 (적립식예금)
"""

from __future__ import annotations

from typing import Iterator

from playwright.sync_api import Page

from ..base import ItemTrigger

# 링크 텍스트에 아래 키워드가 포함되어 있으면 해당 doc_type으로 판별한다.
# 예금거래기본약관/적립식예금약관처럼 공통 문서는 텍스트가 고정이지만,
# 특약/상품설명서는 "KB내맘대로적금 특약"처럼 상품명이 앞에 붙어서 나오므로
# 완전일치가 아니라 포함 여부로 봐야 한다.
# 매핑 키워드가 하나도 없는 링크(예: "공시자료변경")도 일단 클릭은 시도하되, doc_type은 None.
DOC_TYPE_MAP = {
    "예금거래기본약관": "기본약관",
    "적립식예금약관": "기본약관",
    "거치식예금약관": "기본약관",
    "특약": "특약",
    "상품설명서": "상품설명서",
}


def _resolve_doc_type(link_text: str) -> str | None:
    for keyword, doc_type in DOC_TYPE_MAP.items():
        if keyword in link_text:
            return doc_type
    return None

ROW_SELECTOR = "#b054049 > div.n_pcontZn > form > div.n_prodList > table.tType01 > tbody > tr"  # TODO: 실제 테이블 selector로 교체
PRODUCT_NAME_SELECTOR = "th.th01 a"  # TODO: 실제 selector로 교체
DOC_LINK_SELECTOR = "td.tLeft a"  # TODO: 실제 selector로 교체
# 페이지 번호가 <a>가 아니라 폼별 제출 버튼으로 되어 있음:
#   <form onsubmit="return goPage(N);">
#     <input type="hidden" name="NEXT_TAG_PAGE" value="N">
#     <input type="submit" value="N" title="N페이지">
#   </form>
# 번호는 텍스트가 아니라 value 속성에 있어서 inner_text() 대신 get_attribute("value")로 비교해야 함.
PAGE_NUMBER_SELECTOR = "div.paging input[type=submit]"


def _click_link(page: Page, link_locator) -> None:
    """href="#none" + onclick으로 다운로드가 트리거되는 것으로 보임.
    실제 onclick 핸들러(함수명/파라미터)를 확인한 뒤 구현해야 한다."""
    link_locator.click()


def _find_page_link(page: Page, page_number: int):
    """페이지 번호 제출 버튼들 중 value가 page_number와 일치하는 것을 찾는다. 없으면 None."""
    for button in page.locator(PAGE_NUMBER_SELECTOR).all():
        if button.get_attribute("value") == str(page_number):
            return button
    return None


def iter_item_triggers(page: Page) -> Iterator[ItemTrigger]:
    current_page = 1
    while True:
        rows = page.locator(ROW_SELECTOR).all()
        for row in rows:
            product_name = row.locator(PRODUCT_NAME_SELECTOR).inner_text().strip()

            for link in row.locator(DOC_LINK_SELECTOR).all():
                link_text = link.inner_text().strip()
                doc_type = _resolve_doc_type(link_text)

                def click(p: Page, link=link) -> None:
                    _click_link(p, link)

                yield ItemTrigger(
                    raw_title=f"{product_name}_{link_text}",
                    click=click,
                    doc_type=doc_type,
                )

        next_page_link = _find_page_link(page, current_page + 1)
        if next_page_link is None:
            break
        next_page_link.click()
        page.wait_for_load_state("networkidle")
        current_page += 1
