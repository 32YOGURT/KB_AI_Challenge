"""상품설명서(및 doc_type 미판별 문서)용 청커: markdown heading(#) 단위로 청킹한다.

사용법(단독 실행 시 스모크 테스트):
    python scripts/rag/section_chunker.py <PDF 경로>
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.stdout.reconfigure(encoding="utf-8")

_HEADING_RE = re.compile(r"^#{1,6}\s+(.*)$", re.MULTILINE)
_MIN_SECTION_LEN = 30  # 라벨만 있고 본문이 거의 없는 섹션은 다음 섹션에 흡수한다.


def chunk_sections(pages: list[dict]) -> list[dict]:
    """pages는 scripts/rag/pdf_to_markdown.convert_pdf()의 반환값
    ([{"page_number": int, "markdown": str}, ...])을 그대로 받는다.

    반환: [{"clause_title": str, "text": str, "page": int}, ...]
    """
    full_text = ""
    offsets: list[tuple[int, int]] = []  # (문자 오프셋, 그 오프셋이 속한 page_number)
    for page in pages:
        offsets.append((len(full_text), page["page_number"]))
        full_text += page["markdown"] + "\n"

    def _page_for_offset(offset: int) -> int:
        page_number = offsets[0][1]
        for off, pn in offsets:
            if off <= offset:
                page_number = pn
            else:
                break
        return page_number

    headings = [(m.start(), m.group(1).strip()) for m in _HEADING_RE.finditer(full_text)]
    if not headings:
        # heading이 하나도 없는 문서(표 위주 스캔본 등) — 문서 전체를 한 청크로 취급한다.
        text = full_text.strip()
        return [{"clause_title": "전체", "text": text, "page": pages[0]["page_number"]}] if text else []

    boundaries: list[tuple[int, str]] = []
    if headings[0][0] > 0:
        boundaries.append((0, "표지"))  # 첫 heading 이전 내용(심의필 번호 등 표지)도 한 섹션으로 취급
    boundaries.extend(headings)

    raw_sections = []
    for i, (start, title) in enumerate(boundaries):
        stop = boundaries[i + 1][0] if i + 1 < len(boundaries) else len(full_text)
        raw_sections.append((start, title, full_text[start:stop].strip()))

    # 짧은 섹션은 다음 섹션 앞에 이어붙여서 미니 청크가 남지 않게 한다.
    merged: list[tuple[int, str, str]] = []
    pending = ""
    for i, (start, title, text) in enumerate(raw_sections):
        is_last = i == len(raw_sections) - 1
        if len(text) < _MIN_SECTION_LEN and not is_last:
            pending += text + "\n"
            continue
        merged.append((start, title, (pending + text).strip()))
        pending = ""
    if pending and merged:
        # 마지막 섹션까지 전부 짧았던 경우, 직전에 만든 청크에 흡수시킨다.
        last_start, last_title, last_text = merged[-1]
        merged[-1] = (last_start, last_title, (last_text + "\n" + pending).strip())
    elif pending:
        # 문서 전체가 전부 짧은 섹션뿐이었던 극단적인 경우 — 그대로 하나의 청크로 남긴다.
        merged.append((0, "전체", pending.strip()))

    return [
        {"clause_title": title, "text": text, "page": _page_for_offset(start)}
        for start, title, text in merged
        if text
    ]


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("사용법: python scripts/rag/section_chunker.py <PDF 경로>")
        sys.exit(1)

    from scripts.rag.pdf_to_markdown import convert_pdf

    pages = convert_pdf(sys.argv[1])
    chunks = chunk_sections(pages)
    print(f"{len(chunks)}개 섹션 청크 추출됨\n")
    for c in chunks:
        print(f"--- {c['clause_title']} (p.{c['page']}) ---")
        print(c["text"])
        print()
