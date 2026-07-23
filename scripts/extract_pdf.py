"""PDF에서 페이지 단위로 텍스트/표를 추출한다.

사용법:
    python scripts/extract_pdf.py <PDF 경로>

결과는 콘솔 요약 출력 + results/<PDF 파일명>.json 저장.
"""

import json
import sys
from pathlib import Path

import pdfplumber

# Windows 콘솔 기본 인코딩(cp949)에서 한글/특수문자 출력 시 깨짐 방지
sys.stdout.reconfigure(encoding="utf-8")

RESULTS_DIR = Path(__file__).parent.parent / "results"


def extract_pdf_pages(pdf_path: str | Path, extract_tables: bool = True) -> list[dict]:
    """PDF를 페이지 단위로 추출한다.

    각 페이지는 {page_number, text, tables} 딕셔너리.
    text가 비어 있으면 스캔본(이미지 PDF)일 가능성이 높다는 신호.
    extract_tables=False면 표 추출을 건너뛰어 속도를 높인다(텍스트만 필요할 때).
    """
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            tables = page.extract_tables() if extract_tables else []
            pages.append({
                "page_number": i,
                "text": text,
                "tables": tables,
            })
    return pages


def _save_results(pdf_path: str, pages: list[dict]) -> Path:
    RESULTS_DIR.mkdir(exist_ok=True)
    out_path = RESULTS_DIR / f"{Path(pdf_path).stem}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"source": pdf_path, "pages": pages}, f, ensure_ascii=False, indent=2)
    return out_path


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("사용법: python scripts/extract_pdf.py <PDF 경로>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    pages = extract_pdf_pages(pdf_path)
    out_path = _save_results(pdf_path, pages)
    print(f"\n저장됨: {out_path}")
