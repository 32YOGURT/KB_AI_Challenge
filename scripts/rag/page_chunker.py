"""상품설명서(및 doc_type 미판별 문서)용 청커: 페이지 단위로 청킹한다.

조항(제N조) 같은 명확한 단위가 없고 Q&A/번호 섹션/표가 뒤섞여 있어서, 우선 가장 단순한
기준인 "페이지 하나 = 청크 하나"로 시작한다. heading 단위 청킹(더 잘게, 정밀하게 자르되
표가 페이지 여러 장에 걸쳐 이어지면 청크가 과도하게 커질 수 있음)과 비교해서 실제 검색
품질을 본 뒤 필요하면 바꾸기로 함 — 지금은 성능 비교를 위한 베이스라인.

사용법(단독 실행 시 스모크 테스트):
    python scripts/rag/page_chunker.py <PDF 경로>
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.stdout.reconfigure(encoding="utf-8")

_MIN_CHUNK_LEN = 30  # 표지 등 텍스트가 거의 없는 페이지는 건너뛴다.


def chunk_pages(pages: list[dict]) -> list[dict]:
    """pages는 scripts/rag/pdf_to_markdown.convert_pdf()의 반환값
    ([{"page_number": int, "markdown": str}, ...])을 그대로 받는다.

    반환: [{"clause_title": str, "text": str, "page": int}, ...]
    """
    chunks = []
    for page in pages:
        text = page["markdown"].strip()
        if len(text) < _MIN_CHUNK_LEN:
            continue
        chunks.append(
            {
                "clause_title": f"{page['page_number']}페이지",
                "text": text,
                "page": page["page_number"],
            }
        )
    return chunks


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("사용법: python scripts/rag/page_chunker.py <PDF 경로>")
        sys.exit(1)

    from scripts.rag.pdf_to_markdown import convert_pdf

    pages = convert_pdf(sys.argv[1])
    chunks = chunk_pages(pages)
    print(f"{len(chunks)}개 페이지 청크 추출됨\n")
    for c in chunks:
        print(f"--- {c['clause_title']} ---")
        print(c["text"])
        print()
