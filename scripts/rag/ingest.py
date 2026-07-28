"""crawled_data/manifest.json 전체를 doc_type에 따라 알맞은 청커로 청킹하고 Qdrant
`product_clauses` 컬렉션에 인덱싱하는 오케스트레이터.

doc_type별 분기:
- 기본약관/특약/약정서 -> scripts/rag/clause_chunker.chunk_clauses (제N조 단위)
- 상품설명서 및 doc_type 미판별 문서 -> scripts/rag/page_chunker.chunk_pages (페이지 단위)

표는 이미 scripts/rag/pdf_to_markdown.py에서 Docling이 markdown 표로 변환해두므로 별도
평탄화가 필요 없다 (기존 pdfplumber 기반 계획과 다른 점).

사용법:
    python scripts/rag/ingest.py               # 전체 인덱싱 (임베딩 API 호출 발생)
    python scripts/rag/ingest.py --dry-run      # 임베딩/업서트 없이 청킹 결과만 출력
    python scripts/rag/ingest.py --limit 20     # 앞 N개 manifest 엔트리만 처리 (검증용)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.stdout.reconfigure(encoding="utf-8")

from app.schemas import ClauseChunk  # noqa: E402
from app.services.rag.retrieval import upsert_clauses  # noqa: E402
from scripts.crawl.manifest import CRAWLED_DATA_DIR, MANIFEST_PATH  # noqa: E402
from scripts.rag.clause_chunker import chunk_clauses  # noqa: E402
from scripts.rag.page_chunker import chunk_pages  # noqa: E402
from scripts.rag.pdf_to_markdown import convert_pdf  # noqa: E402

CLAUSE_DOC_TYPES = {"기본약관", "특약", "약정서"}

_TABLE_ROW_RE = re.compile(r"^\|[-:\s|]+\|$", re.MULTILINE)
_EFFECTIVE_DATE_RE = re.compile(
    r"(\d{4})[.\s년]\s*(\d{1,2})[.\s월]\s*(\d{1,2})\s*일?\s*(?:이후)?\s*부터\s*(?:적용|시행)"
)


def _extract_effective_date(pages: list[dict]) -> str | None:
    """부칙의 "YYYY.MM.DD부터 시행/적용합니다" 문구에서 날짜를 뽑는다. 부칙이 여러 번
    쌓여있으면(개정 이력) 문서 내 마지막 매치를 최신 시행일로 간주한다."""
    full_text = "\n".join(p["markdown"] for p in pages)
    matches = _EFFECTIVE_DATE_RE.findall(full_text)
    if not matches:
        return None
    year, month, day = matches[-1]
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def build_chunks(entry: dict) -> list[ClauseChunk]:
    pdf_path = CRAWLED_DATA_DIR / entry["saved_path"]
    pages = convert_pdf(pdf_path)
    if not pages:
        return []

    # doc_type 판별 불가(상품명=링크텍스트, 동의서/안내문 등)는 상품설명서와 동일하게
    # 페이지 단위로 청킹한다 (조항 번호 체계를 가정할 수 없으므로).
    doc_type = entry["doc_type"] or "상품설명서"

    if doc_type in CLAUSE_DOC_TYPES:
        raw_chunks = chunk_clauses(pages)
        effective_date = _extract_effective_date(pages)
    else:
        raw_chunks = chunk_pages(pages)
        effective_date = None

    source_file = Path(entry["saved_path"]).name
    label = entry["product_name"] or entry["company"]

    result = []
    for c in raw_chunks:
        text = c["text"]
        result.append(
            ClauseChunk(
                product_id=entry["product_id"],
                company=entry["company"],
                category=entry["category"],
                doc_type=doc_type,
                clause_title=c["clause_title"],
                text=text,
                source=f"{label} {c['clause_title']}",
                source_file=source_file,
                page=c["page"],
                effective_date=effective_date,
                content_hash=hashlib.sha256(text.encode("utf-8")).hexdigest(),
                has_table=bool(_TABLE_ROW_RE.search(text)),
            )
        )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="임베딩/업서트 없이 청킹 결과만 출력")
    parser.add_argument("--limit", type=int, default=None, help="앞 N개 manifest 엔트리만 처리")
    args = parser.parse_args()

    entries = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if args.limit:
        entries = entries[: args.limit]

    total_chunks = 0
    skipped_missing_pdf = 0
    failed: list[tuple[str, str]] = []

    for i, entry in enumerate(entries, start=1):
        pdf_path = CRAWLED_DATA_DIR / entry["saved_path"]
        if not pdf_path.exists():
            skipped_missing_pdf += 1
            continue

        try:
            chunks = build_chunks(entry)
        except Exception as e:  # noqa: BLE001 - 개별 PDF 실패가 전체 색인을 막지 않게 한다.
            failed.append((entry["raw_title"], repr(e)))
            continue

        total_chunks += len(chunks)
        tag = f"[{i}/{len(entries)}] {entry['company']} {entry['raw_title']} ({entry['doc_type']})"

        if args.dry_run:
            print(f"{tag} -> {len(chunks)}개 청크")
            for c in chunks[:2]:
                preview = c.text[:80].replace("\n", " ")
                print(f"    - {c.clause_title}: {preview}...")
        else:
            if chunks:
                upsert_clauses(chunks)
            print(f"{tag} -> {len(chunks)}개 청크 색인 완료")

    print(
        f"\n총 {total_chunks}개 청크 {'생성' if args.dry_run else '색인'} 완료 "
        f"(문서 {len(entries)}개 중 PDF 없음 {skipped_missing_pdf}개, 파싱 실패 {len(failed)}개)"
    )
    for title, err in failed[:20]:
        print(f"  실패: {title}: {err}")


if __name__ == "__main__":
    main()
