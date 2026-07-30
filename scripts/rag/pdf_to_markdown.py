"""PDF를 페이지 단위 markdown으로 변환하는 공통 전처리. doc_type별 청커(조항 청킹,
페이지 청킹)가 전부 이 위의 결과물을 입력으로 받는다.

pdfplumber 대신 Docling(레이아웃 분석 + 표 구조 인식 모델)을 쓴다 — 실제 표가 많은
상품설명서/특약 문서에서 pdfplumber는 표를 셀이 깨진 상태로 뽑아내는 반면(예:
KB두근두근여행적금 특약의 우대이율 표), Docling은 markdown 표로 정확하게 복원한다.
덤으로 페이지마다 반복되는 머리말/꼬리말(심의필 번호 등)도 레이아웃 분석 과정에서
자연히 걸러진다.

백엔드로 기본값(DoclingParseV4) 대신 PyPdfiumDocumentBackend를 쓰는 이유: 이 프로젝트
경로에 한글이 섞여 있어서(Windows 사용자 프로필 경로), 기본 백엔드(docling-parse, C++
확장)가 자체 리소스 파일(glyph 데이터 등) 경로를 못 찾는 인코딩 버그가 있었다
(`docling_parse`가 non-ASCII 경로를 못 여는 것으로 보임). PyPdfium 백엔드는 이 문제가
없다.

OCR은 끈다 — 크롤링된 PDF는 전부 텍스트 레이어가 있는 디지털 문서라 불필요하고, OCR을
켜면 페이지당 처리 시간이 크게 늘어난다. 스캔본(이미지 PDF)이 섞여 있다면 해당 문서는
빈 텍스트로 나올 수 있는데, 지금까지 확인한 샘플에서는 전부 텍스트 레이어가 있었다.

사용법(단독 실행 시 스모크 테스트):
    python scripts/rag/pdf_to_markdown.py <PDF 경로>
"""

from __future__ import annotations

import hashlib
import json
import sys
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.stdout.reconfigure(encoding="utf-8")

# 파싱 결과(페이지 markdown) 캐시. crawled_data 하위라 이미 .gitignore 대상이다.
PARSE_CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "crawled_data" / ".parse_cache"

from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend  # noqa: E402
from docling.datamodel.base_models import InputFormat  # noqa: E402
from docling.datamodel.pipeline_options import PdfPipelineOptions  # noqa: E402
from docling.document_converter import DocumentConverter, PdfFormatOption  # noqa: E402


@lru_cache
def _get_converter() -> DocumentConverter:
    """모델 로딩 비용이 커서 프로세스당 한 번만 만들어 재사용한다."""
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = False
    pipeline_options.do_table_structure = True

    return DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=pipeline_options,
                backend=PyPdfiumDocumentBackend,
            )
        }
    )


def _convert(pdf_path: Path) -> list[dict]:
    result = _get_converter().convert(pdf_path)
    doc = result.document

    return [
        {"page_number": page_no, "markdown": doc.export_to_markdown(page_no=page_no)}
        for page_no in sorted(doc.pages.keys())
    ]


def convert_pdf(pdf_path: str | Path) -> list[dict]:
    """PDF를 페이지 단위 markdown 리스트로 변환한다. 결과는 파일 내용 해시를 키로 디스크에
    캐시한다.

    캐시가 필요한 이유: 예금거래기본약관 같은 공통 약관이 상품별 폴더에 각각 저장돼서,
    파일 경로는 달라도 내용이 완전히 같은 PDF가 최대 39번까지 중복 존재한다. 파싱은
    문서당 평균 8.7초라 중복만으로 30분 가까이 낭비된다. 경로가 아니라 내용 해시를
    키로 삼아야 이런 사본들이 같은 캐시를 공유한다.

    반환: [{"page_number": int, "markdown": str}, ...]
    """
    pdf_path = Path(pdf_path)
    digest = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
    cache_file = PARSE_CACHE_DIR / f"{digest}.json"

    if cache_file.exists():
        return json.loads(cache_file.read_text(encoding="utf-8"))

    pages = _convert(pdf_path)
    PARSE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(pages, ensure_ascii=False), encoding="utf-8")
    return pages


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("사용법: python scripts/rag/pdf_to_markdown.py <PDF 경로>")
        sys.exit(1)

    pages = convert_pdf(sys.argv[1])
    print(f"{len(pages)}페이지 변환 완료\n")
    for p in pages:
        print(f"--- page {p['page_number']} ({len(p['markdown'])}자) ---")
        print(p["markdown"])
        print()
