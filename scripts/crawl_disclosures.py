"""공시실 목록 페이지에서 상품설명서/약관 PDF를 다운로드한다.

scripts/crawl/config.json에 등록된 URL(company, doc_type, category)마다
도메인에 맞는 adapter(scripts/crawl/adapters/)를 찾아 실행하고,
결과 PDF는 crawled_data/, 메타데이터는 crawled_data/manifest.json에 저장한다.

사용법:
    python scripts/crawl_disclosures.py

TODO: 구현 예정.
"""
