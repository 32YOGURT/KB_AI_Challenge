"""crawled_data/manifest.json 전체를 doc_type에 따라 알맞은 청커로 청킹하고 Qdrant
`product_clauses` 컬렉션에 인덱싱하는 오케스트레이터.

doc_type별 분기:
- 기본약관/특약/약정서 -> scripts/rag/clause_chunker.chunk_clauses (제N조 단위)
- 상품설명서 및 doc_type 미판별 문서 -> scripts/rag/section_chunker.chunk_sections (heading 단위)

표는 이미 scripts/rag/pdf_to_markdown.py에서 Docling이 markdown 표로 변환해두므로 별도
평탄화가 필요 없다 (기존 pdfplumber 기반 계획과 다른 점).

사용법:
    python scripts/rag/ingest.py                        # 전체 인덱싱 (임베딩 API 호출 발생)
    python scripts/rag/ingest.py --category 예금,적금    # 해당 카테고리만 인덱싱
    python scripts/rag/ingest.py --dry-run              # 임베딩/업서트 없이 청킹 결과만 출력
    python scripts/rag/ingest.py --limit 20             # 앞 N개 manifest 엔트리만 처리 (검증용)

    # 예금/적금 중 상품 10개 + 해당 회사 공통 약관만 색인 (데모용 최소 셋)
    python scripts/rag/ingest.py --category 예금,적금 --max-products 10
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

from app.clients import minio_client  # noqa: E402
from app.schemas import ClauseChunk  # noqa: E402
from app.services.rag.embeddings import split_for_embedding  # noqa: E402
from app.services.rag.retrieval import upsert_clauses  # noqa: E402
from scripts.crawl.manifest import CRAWLED_DATA_DIR, MANIFEST_PATH  # noqa: E402
from scripts.rag.clause_chunker import chunk_clauses  # noqa: E402
from scripts.rag.section_chunker import chunk_sections  # noqa: E402
from scripts.rag.pdf_to_markdown import convert_pdf  # noqa: E402

CLAUSE_DOC_TYPES = {"기본약관", "특약", "약정서"}

# entry["saved_path"]는 이제 로컬 경로가 아니라 MinIO object key라, 파싱 전에 여기로
# 내려받아 캐싱한다 (docling이 실제 파일 경로를 요구하고, 재실행 시 재다운로드도 피함).
_MINIO_CACHE_DIR = CRAWLED_DATA_DIR / ".minio_cache"


def _local_pdf_path(entry: dict) -> Path:
    return _MINIO_CACHE_DIR / entry["saved_path"]


def _ensure_pdf_downloaded(entry: dict) -> Path:
    pdf_path = _local_pdf_path(entry)
    if not pdf_path.exists():
        minio_client.download_to_path(entry["saved_path"], pdf_path)
    return pdf_path

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
    pdf_path = _local_pdf_path(entry)
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
        raw_chunks = chunk_sections(pages)
        effective_date = None

    source_file = Path(entry["saved_path"]).name
    # 공통 약관(product_id 없음)은 회사 전체에 적용되므로 상품명을 출처로 쓰면 안 된다 —
    # 사본 중 마지막에 처리된 상품 이름이 박혀서 엉뚱한 상품이 출처로 표시된다.
    label = entry["product_name"] if entry["product_id"] else entry["company"]

    result = []
    for c in raw_chunks:
        # 조항/heading 단위 청킹으로도 여전히 임베딩 API 토큰 상한(8192)을 넘는 드문
        # 경우(예: heading 하나에 거대한 표가 통째로 붙은 문서)가 있어, 넘으면 여기서
        # 추가로 쪼갠다 — 대부분은 pieces가 1개라 아무 영향 없다.
        pieces = split_for_embedding(c["text"])
        for i, text in enumerate(pieces):
            clause_title = c["clause_title"] + (f" ({i + 1}/{len(pieces)})" if len(pieces) > 1 else "")
            result.append(
                ClauseChunk(
                    product_id=entry["product_id"],
                    company=entry["company"],
                    category=entry["category"],
                    doc_type=doc_type,
                    clause_title=clause_title,
                    text=text,
                    source=f"{label} {clause_title}",
                    source_file=source_file,
                    page=c["page"],
                    effective_date=effective_date,
                    content_hash=hashlib.sha256(text.encode("utf-8")).hexdigest(),
                    has_table=bool(_TABLE_ROW_RE.search(text)),
                )
            )
    return result


def _filter_products(parser: argparse.ArgumentParser, entries: list[dict], args) -> list[dict]:
    """지정된 상품의 문서 + 그 상품이 속한 회사의 공통 약관(product_id=None)만 남긴다.

    공통 약관을 함께 넣는 이유: 중도해지 이율, 예금자보호 같은 핵심 조항은 상품별 특약이
    아니라 회사 공통 기본약관(예금거래기본약관 등)에 있고, 검색 쪽(retrieval.search_clauses)도
    product_id 일치 문서와 product_id=None 문서를 함께 조회하도록 되어 있다. 상품 문서만
    색인하면 검색은 되지만 정작 핵심 조항이 빠진다.
    """
    if args.product_id:
        selected = {p.strip() for p in args.product_id.split(",") if p.strip()}
        known = {e["product_id"] for e in entries if e["product_id"]}
        unknown = selected - known
        if unknown:
            parser.error(f"필터 결과에 없는 product_id: {sorted(unknown)}")
    else:
        selected = list(dict.fromkeys(e["product_id"] for e in entries if e["product_id"]))
        selected = set(selected[: args.max_products])

    companies = {e["company"] for e in entries if e["product_id"] in selected}
    kept = [
        e for e in entries if e["product_id"] in selected or (not e["product_id"] and e["company"] in companies)
    ]

    product_docs = sum(1 for e in kept if e["product_id"])
    names = sorted({e["product_name"] for e in kept if e["product_id"]})
    print(f"상품 {len(selected)}개 필터 -> 상품 문서 {product_docs}개 + 공통 약관 {len(kept) - product_docs}개")
    for name in names:
        print(f"    - {name}")
    return kept


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="임베딩/업서트 없이 청킹 결과만 출력")
    parser.add_argument("--limit", type=int, default=None, help="앞 N개 manifest 엔트리만 처리")
    parser.add_argument(
        "--category",
        default=None,
        help="쉼표로 구분한 카테고리만 처리 (예: '예금,적금'). 미지정 시 manifest 전체",
    )
    parser.add_argument(
        "--max-products",
        type=int,
        default=None,
        help="상품 N개까지만 처리 (manifest 순서). 회사 공통 약관은 자동 포함",
    )
    parser.add_argument(
        "--product-id",
        default=None,
        help="쉼표로 구분한 product_id만 처리. 회사 공통 약관은 자동 포함",
    )
    args = parser.parse_args()

    entries = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    if args.category:
        wanted = {c.strip() for c in args.category.split(",") if c.strip()}
        available = sorted({e["category"] for e in entries})
        unknown = wanted - set(available)
        if unknown:
            parser.error(f"manifest에 없는 카테고리: {sorted(unknown)} (가능: {available})")
        entries = [e for e in entries if e["category"] in wanted]
        print(f"카테고리 {sorted(wanted)} 필터 -> 문서 {len(entries)}개")

    if args.max_products or args.product_id:
        entries = _filter_products(parser, entries, args)

    if args.limit:
        entries = entries[: args.limit]

    total_chunks = 0
    skipped_missing_pdf = 0
    skipped_duplicate = 0
    failed: list[tuple[str, str]] = []
    # 이미 처리한 청크의 content_hash. 공통 약관이 상품별로 중복 저장돼 있어서 같은 조항이
    # 수십 번 다시 올라오는데, point id 자체가 content_hash에서 나오므로 두 번째 이후는 같은
    # point를 덮어쓰는 것뿐이다 — 임베딩 API 호출만 헛돈다(실측 1915개 중 유니크 248개).
    seen_hashes: set[str] = set()

    for i, entry in enumerate(entries, start=1):
        try:
            _ensure_pdf_downloaded(entry)
        except Exception:  # noqa: BLE001 - MinIO에 해당 object가 없거나 접속 실패
            skipped_missing_pdf += 1
            continue

        try:
            chunks = build_chunks(entry)
        except Exception as e:  # noqa: BLE001 - 개별 PDF 실패가 전체 색인을 막지 않게 한다.
            failed.append((entry["raw_title"], repr(e)))
            continue

        new_chunks = [c for c in chunks if c.content_hash not in seen_hashes]
        skipped_duplicate += len(chunks) - len(new_chunks)
        seen_hashes.update(c.content_hash for c in new_chunks)
        chunks = new_chunks

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
        f"(문서 {len(entries)}개 중 PDF 없음 {skipped_missing_pdf}개, 파싱 실패 {len(failed)}개, "
        f"중복 청크 스킵 {skipped_duplicate}개)"
    )
    for title, err in failed[:20]:
        print(f"  실패: {title}: {err}")


if __name__ == "__main__":
    main()
