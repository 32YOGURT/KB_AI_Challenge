"""수동 시드 데이터(app/data/clause_seed.json)를 임베딩해서 Qdrant `product_clauses`
컬렉션에 upsert한다. PDF 파싱 파이프라인이 만들어지기 전까지, 검색/LLM 추론 로직을
검증하기 위한 임시 데이터.

사용법:
    python scripts/seed_clauses.py
"""

import hashlib
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.schemas import ClauseChunk  # noqa: E402
from app.services.rag.retrieval import upsert_clauses  # noqa: E402

SEED_PATH = Path(__file__).parent.parent / "app" / "data" / "clause_seed.json"


def _load_chunks() -> list[ClauseChunk]:
    raw = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    chunks = []
    for entry in raw:
        content_hash = hashlib.sha256(entry["text"].encode("utf-8")).hexdigest()
        chunks.append(ClauseChunk(**entry, content_hash=content_hash))
    return chunks


if __name__ == "__main__":
    chunks = _load_chunks()
    upsert_clauses(chunks)
    print(f"{len(chunks)}개 조항 인덱싱 완료 -> Qdrant `product_clauses`")
