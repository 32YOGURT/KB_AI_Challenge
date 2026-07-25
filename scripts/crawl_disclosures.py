"""공시실 목록 페이지에서 상품설명서/약관 PDF를 다운로드한다.

scripts/crawl/config.json에 등록된 URL(company, doc_type, category, adapter)마다
도메인에 맞는 adapter(scripts/crawl/adapters/)를 찾아 실행하고,
결과 PDF는 crawled_data/, 메타데이터는 crawled_data/manifest.json에 저장한다.

사용법:
    python scripts/crawl_disclosures.py
"""

import sys
from pathlib import Path

# Windows 콘솔 기본 인코딩(cp949)에서 한글 출력 시 깨짐 방지
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.crawl import base  # noqa: E402

CONFIG_PATH = Path(__file__).parent / "crawl" / "config.json"

if __name__ == "__main__":
    # headless=False: 실제 클릭이 다운로드로 이어지는지 눈으로 확인하기 위해
    # 검증 끝나면 True로 바꿔도 됨.
    base.run(CONFIG_PATH, headless=False)
