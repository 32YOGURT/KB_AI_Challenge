1. PDF 추출할 때, 테이블 잘 구조화해서 임베딩하기

2. 실제 데이터 수집하는 수집 파이프라인 구성하기 (스크립트)
   [1. Target URL 수집] ──► [2. PDF 다운로더] ──► [3. PDF Text Extractor] ──► [4. Cleaning & Chunking]
   (공시실 게시판 파싱) (httpx / Playwright) (PyMuPDF / LlamaParse) (Markdown 변환 / Vector DB)

3. 지금 RAG + AI 파이프라인은 진짜 scaffold니까 차후에 로직은 개선 필요
