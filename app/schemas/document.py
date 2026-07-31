from pydantic import BaseModel


class PresignedDocument(BaseModel):
    """원문 PDF를 브라우저가 직접 받아갈 수 있는 임시 URL."""

    url: str
    expires_in: int  # 초
