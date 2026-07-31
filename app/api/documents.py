from datetime import timedelta

from fastapi import APIRouter, HTTPException, Query

from app.clients import object_storage
from app.schemas.document import PresignedDocument

router = APIRouter(prefix="/api/documents", tags=["documents"])

PRESIGN_TTL = timedelta(minutes=10)


@router.get("/presign", response_model=PresignedDocument)
def presign_document(key: str = Query(..., description="MinIO object key (ClauseChunk.source_key)")) -> PresignedDocument:
    url = object_storage.presign_get(key, PRESIGN_TTL)
    if url is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return PresignedDocument(url=url, expires_in=int(PRESIGN_TTL.total_seconds()))
