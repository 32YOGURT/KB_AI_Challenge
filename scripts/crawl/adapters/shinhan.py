"""신한은행 상품설명서/약관 자료실 어댑터.

목록은 WebSquare "grid" 위젯(<table> 아님)이라 한 행이 <tr class="grid_body_row">,
셀은 col_id 속성으로 구분된다: C_PROD_NAME(상품명), C_PROD_ID(문서 버튼들).

문서 버튼(<button onclick="shbObj.fncNewGridFromBtnClick(...)">)을 클릭하면 브라우저
다운로드나 새 창이 뜨는 게 아니라, AJAX 요청(/serviceEndpoint/httpDigital)이 나가고
그 JSON 응답의 dataBody.RESULT_LIST 안에 실제 PDF URL(PDF_FILE_NM)이 들어있다.
그래서 이 어댑터는 클릭 → 그 응답을 가로채서 URL 추출 → HTTP GET으로 직접 받는 방식이다
(클릭이 여는 새 창/다운로드 이벤트를 기다리는 게 아님).

참고 페이지: https://www.shinhan.com/hpe/index.jsp#050504090100 (저축상품-적립식예금)
"""

from __future__ import annotations

from typing import Iterator

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from ..base import DEFAULT_TIMEOUT_MS, ItemTrigger

# 링크 텍스트에 아래 키워드가 포함되어 있으면 해당 doc_type으로 판별한다 (KB와 동일한 이유:
# 특약/상품설명서는 "신한 청년미래적금 특약"처럼 상품명이 앞에 붙어서 나옴).
DOC_TYPE_MAP = {
    "특약": "특약",
    "상품설명서": "상품설명서",
    # "입출금이자유로운예금약관"처럼 실제 링크 텍스트는 종류가 다양해서 개별 나열 대신
    # "약관"을 마지막 catch-all로 둔다 (하나은행 어댑터와 동일 패턴).
    "약관": "기본약관",
}


def _resolve_doc_type(link_text: str) -> str | None:
    for keyword, doc_type in DOC_TYPE_MAP.items():
        if keyword in link_text:
            return doc_type
    return None


# grid의 id(grd_자료실 등)는 5개 카테고리 페이지 전부에서 동일하게 확인됨.
# 한 페이지에 8개씩 보여주는데 .grid_body_row가 그보다 더 잡힐 때가 있음 — WebSquare가
# 내부적으로 들고 있는 숨겨진 여분/템플릿 행으로 보여서 :visible로 걸러낸다.
ROW_SELECTOR = "#grd_자료실 .grid_body_row:visible"
PRODUCT_NAME_SELECTOR = 'td[col_id="C_PROD_NAME"]'
DOC_LINK_SELECTOR = 'td[col_id="C_PROD_ID"] button'
# 페이지 번호가 실제 <a>로 되어 있음: <a class="w2pageList_control_label" index="N">N</a>
# KB와 달리 한 번에 여러 개(10개 등) 안 보이고 배치 넘김(맨앞/이전/다음/맨뒤) 버튼이 따로 있는데,
# 그 배치 넘김은 아직 처리 안 함 (페이지가 그 이상 많은 카테고리에서 확인 필요).
PAGE_NUMBER_SELECTOR = "#pl_pageNav a.w2pageList_control_label"


def _close_popup_if_any(page: Page) -> None:
    """문서 버튼 클릭은 실제로 새 창이 아니라 페이지 안 오버레이 팝업(시행일별 PDF 목록)을
    띄운다. 이 팝업을 안 치우면 다음 버튼 클릭이 막혀서(응답 자체가 안 뜸) 계속 실패한다.

    닫기 버튼을 클릭하는 방식은 두 가지 문제가 있었다: (1) 진짜 닫기 버튼을 못 찾는 경우가
    있었고(class는 다른 종류 레이어 것과 겹침), (2) 클릭해도 DOM에서 실제로 제거되는 게
    아니라 숨겨지기만 해서 수십~수백 번 누적되면 브라우저가 크래시났다. 그래서 클릭 대신
    JS로 팝업 DOM 자체를 직접 삭제한다 — 다음 클릭도 안 막히고 메모리도 안 쌓인다.

    팝업은 AJAX 응답을 받은 뒤 콜백이 DOM에 그리는 것이라 살짝 늦게 나타날 수 있어 잠깐 기다린다."""
    page.wait_for_timeout(500)
    page.evaluate(
        """() => {
            document.querySelectorAll('.w2popup_window').forEach(el => el.remove());
            document.querySelectorAll('.w2modal').forEach(el => el.remove());
        }"""
    )


def _fetch(page: Page, doc_button) -> bytes | None:
    """클릭 → AJAX 응답 가로채기 → 응답 속 PDF URL을 HTTP GET으로 받아온다.
    끝나면 클릭이 띄운 팝업을 닫아 다음 항목 클릭이 막히지 않게 한다."""
    try:
        try:
            with page.expect_response(
                lambda r: "serviceEndpoint/httpDigital" in r.url, timeout=DEFAULT_TIMEOUT_MS
            ) as response_info:
                doc_button.click(force=True, timeout=DEFAULT_TIMEOUT_MS)
        except PlaywrightTimeoutError:
            return None

        try:
            body = response_info.value.json()
        except Exception:
            return None

        result_list = (body.get("dataBody") or {}).get("RESULT_LIST") or []
        if not result_list:
            return None

        pdf_url = result_list[0].get("PDF_FILE_NM")
        if not pdf_url:
            return None

        try:
            pdf_response = page.context.request.get(pdf_url, timeout=DEFAULT_TIMEOUT_MS)
        except PlaywrightTimeoutError:
            return None
        if not pdf_response.ok:
            return None
        return pdf_response.body()
    finally:
        _close_popup_if_any(page)


def _find_page_link(page: Page, page_number: int):
    for link in page.locator(PAGE_NUMBER_SELECTOR).all():
        if link.inner_text().strip() == str(page_number):
            return link
    return None


def iter_item_triggers(page: Page) -> Iterator[ItemTrigger]:
    # SPA라 grid 데이터가 초기 페이지 로드 이후 별도 AJAX로 비동기 렌더링된다.
    # base.py의 page.goto()는 초기 로드만 기다리므로, 여기서 행이 실제로 뜰 때까지 기다려야 한다.
    page.wait_for_selector(ROW_SELECTOR, timeout=DEFAULT_TIMEOUT_MS)
    # 행이 "존재"하는 시점과 내부 셀 내용까지 완전히 렌더링되는 시점 사이에 살짝 텀이
    # 있어서, 바로 이어서 첫 행을 건드리면 가끔 stale/timeout이 났다. 짧게 더 기다린다.
    page.wait_for_timeout(500)

    current_page = 1
    while True:
        rows = page.locator(ROW_SELECTOR).all()
        for row in rows:
            try:
                product_name = row.locator(PRODUCT_NAME_SELECTOR).inner_text(timeout=DEFAULT_TIMEOUT_MS).strip()
            except PlaywrightTimeoutError:
                continue

            for link in row.locator(DOC_LINK_SELECTOR).all():
                try:
                    link_text = link.inner_text(timeout=DEFAULT_TIMEOUT_MS).strip()
                except PlaywrightTimeoutError:
                    # 이 버튼만 못 읽은 것(예: 행이 막 갱신되는 중). 전체를 죽이지 않고 건너뛴다.
                    continue
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
        # networkidle만으론 부족했음 — 페이지 전환 후 grid가 AJAX로 다시 그려지는 걸
        # 못 기다려서 2페이지부터 행 대부분이 stale/timeout 나는 문제가 있었다.
        # 첫 페이지 진입할 때와 동일하게, 행이 실제로 뜰 때까지 명시적으로 기다린다.
        page.wait_for_selector(ROW_SELECTOR, timeout=DEFAULT_TIMEOUT_MS)
        page.wait_for_timeout(500)
        current_page += 1
