from pydantic import BaseModel


class UserSummary(BaseModel):
    """유저 식별/표시용 최소 정보 (프론트 유저 전환 목록 등). 금융 데이터는 담지 않는다 —
    금융 데이터는 app/schemas/signals/*(마이데이터 신호)에서 가져온다."""

    id: str
    display_name: str
    # 이 체험 프로필이 어떤 성격인지 한 줄 설명. mock 데이터와 같이 관리해야 설명이
    # 실제 값과 어긋나지 않으므로 mydata_mock.json에서 가져온다.
    description: str = ""
