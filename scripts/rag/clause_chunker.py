"""기본약관/특약/약정서용 청커: "제N조" 단위로 청킹한다.

scripts/rag/pdf_to_markdown.py가 만든 페이지별 markdown을 입력으로 받는다. 경계 판단은
두 조건을 동시에 만족하는 줄만 인정한다:
1. markdown heading이다 (줄이 "#"로 시작함) — Docling은 실제로 제목처럼 보이는 요소만
   heading으로 승격시키므로, 본문 중 "제3조에 의해 계산한다"처럼 줄 시작에 우연히 걸리는
   조항 참조(진짜 헤더가 아님)는 애초에 heading이 아니라서 여기서 자동으로 걸러진다.
2. heading 텍스트가 "제N조" 패턴으로 시작한다 — 같은 조항 안에 있는 하위 소제목
   (예: 제7조 특약의 "확인사항", "제공요건 및 제공일")은 heading이긴 해도 이 패턴이
   아니므로 경계로 취급하지 않고 직전 조항 청크에 그대로 흡수된다.

조항이 페이지 경계를 넘어 이어지는 경우가 실제로 있어서(예: 신한 거치식예금특약의
제11조가 2페이지 끝에서 시작해 3페이지로 이어짐), 페이지별로 자르지 않고 문서 전체
markdown을 이어붙인 뒤 정규식으로 자르고, 각 조항이 시작한 페이지 번호를 오프셋으로
역산한다.

부칙(개정 이력, "이 약관은 YYYY.MM.DD부터 시행합니다")은 조항이 아니라 이 문서가 언제
시행되었는지의 메타데이터라서, 마지막 조항 뒤에 붙지 않도록 잘라내고 청킹 대상에서
제외한다. 확인된 샘플들에서는 전부 부칙이 문서 맨 뒤에 몰려있어서, 첫 "부칙" heading을
만나면 그 지점에서 자르고 이후는 더 보지 않는다.

사용법(단독 실행 시 스모크 테스트):
    python scripts/rag/clause_chunker.py <PDF 경로>
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.stdout.reconfigure(encoding="utf-8")

_HEADING_RE = re.compile(r"^#{1,6}\s+(.*)$", re.MULTILINE)
_CLAUSE_TITLE_RE = re.compile(r"^제\s*\d+\s*조")
_APPENDIX_TITLE_RE = re.compile(r"^부\s?칙\s*$")


def chunk_clauses(pages: list[dict]) -> list[dict]:
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

    # heading 줄들을 순회하며 "제N조"만 조항 경계로 채택하고, "부칙"을 만나면
    # 그 지점에서 문서를 잘라 이후는 보지 않는다(부칙은 항상 맨 뒤에 몰려있음).
    clause_headings: list[tuple[int, str]] = []  # (문자 오프셋, clause_title)
    end_offset = len(full_text)
    for m in _HEADING_RE.finditer(full_text):
        title = m.group(1).strip()
        if _APPENDIX_TITLE_RE.match(title):
            end_offset = m.start()
            break
        if _CLAUSE_TITLE_RE.match(title):
            clause_headings.append((m.start(), title))

    chunks = []
    for i, (start, title) in enumerate(clause_headings):
        stop = clause_headings[i + 1][0] if i + 1 < len(clause_headings) else end_offset
        text = full_text[start:stop].strip()
        if not text:
            continue
        chunks.append({"clause_title": title, "text": text, "page": _page_for_offset(start)})
    return chunks


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("사용법: python scripts/rag/clause_chunker.py <PDF 경로>")
        sys.exit(1)

    from scripts.rag.pdf_to_markdown import convert_pdf

    pages = convert_pdf(sys.argv[1])
    chunks = chunk_clauses(pages)
    print(f"{len(chunks)}개 조항 청크 추출됨\n")
    for c in chunks:
        print(f"--- {c['clause_title']} (p.{c['page']}) ---")
        print(c["text"])
        print()
