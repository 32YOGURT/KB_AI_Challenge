"""마이데이터 표준 API 클라이언트의 목업.

실제 마이데이터 API는 인가 제약으로 연동할 수 없어, 실제 요청을 보내지 않고
app/data/mydata_mock.json에서 읽은 데이터를 API 응답 형식 그대로 반환한다.
FSSClient와 동일한 인터페이스 형태(컨텍스트 매니저 등)를 유지해, 추후 실제
마이데이터 API로 교체할 때 내부 구현만 바꾸면 되도록 한다.

인가(토큰 발급/검증)는 app/clients/mydata/auth.py가 담당한다.
데이터 조합/가공(예: 카드 승인내역 → 대중교통/택시 실적 집계)은 여기서 하지
않고 services/ 쪽 책임으로 둔다 — 이 클라이언트는 mock 데이터를 API 형식
그대로 반환하는 것까지만 한다.
"""

from __future__ import annotations

from datetime import datetime

from app.schemas import UserProfile
from app.schemas.mydata.bank_accounts import AccountItem, AccountListResponse
from app.schemas.mydata.bank_accounts_deposit_basic import AccountBasicItem, AccountBasicResponse
from app.schemas.mydata.bank_accounts_deposit_detail import AccountDetailItem, AccountDetailResponse
from app.schemas.mydata.bank_accounts_deposit_transactions import (
    AccountTransactionItem,
    AccountTransactionResponse,
)
from app.schemas.mydata.card_cards import CardItem, CardListResponse
from app.schemas.mydata.card_cards_approval_domestic import CardApprovalItem, CardApprovalResponse
from app.services.store import get_mydata_institution_section, get_mydata_section, list_mydata_institutions
from app.services.store import get_user_profile as _load_user_profile


class MyDataError(Exception):
    """MyData 클라이언트 오류."""


def _now_timestamp() -> str:
    return datetime.now().strftime("%Y%m%d%H%M%S")


class MyDataClient:
    def __init__(self) -> None:
        pass

    def __enter__(self) -> "MyDataClient":
        return self

    def __exit__(self, *exc_info: object) -> None:
        pass

    def _require_profile(self, user_id: str) -> UserProfile:
        profile = _load_user_profile(user_id)
        if profile is None:
            raise MyDataError(f"등록되지 않은 user_id: {user_id!r}")
        return profile

    def get_user_profile(self, user_id: str) -> UserProfile:
        """user_id의 마이데이터 기반 유저 프로필을 반환한다 (목업: 로컬 mock 데이터)."""
        return self._require_profile(user_id)

    def list_institutions(self, user_id: str) -> list[str]:
        """정보제공-공통-002(전송요구 내역 조회)에 대응: user_id가 마이데이터를
        연동(전송요구)한 금융회사(org_code) 목록을 반환한다."""
        self._require_profile(user_id)
        return list_mydata_institutions(user_id)

    def get_bank_accounts(self, user_id: str, org_code: str) -> AccountListResponse:
        """은행-001: 계좌 목록 조회 (기관별 호출)."""
        self._require_profile(user_id)
        items = [
            AccountItem(**raw) for raw in get_mydata_institution_section(user_id, org_code, "accounts")
        ]
        return AccountListResponse(
            rsp_code="000",
            rsp_msg="정상처리",
            search_timestamp=_now_timestamp(),
            reg_date="20250101",
            account_cnt=len(items),
            account_list=items,
        )

    def get_bank_account_basic(self, user_id: str, org_code: str) -> AccountBasicResponse:
        """은행-002: 수신계좌 기본정보 조회 (기관별 호출)."""
        self._require_profile(user_id)
        items = [
            AccountBasicItem(**raw)
            for raw in get_mydata_institution_section(user_id, org_code, "account_basic")
        ]
        return AccountBasicResponse(
            rsp_code="000",
            rsp_msg="정상처리",
            search_timestamp=_now_timestamp(),
            basic_cnt=len(items),
            basic_list=items,
        )

    def get_bank_account_detail(self, user_id: str, org_code: str) -> AccountDetailResponse:
        """은행-003: 수신계좌 추가정보 조회 (기관별 호출)."""
        self._require_profile(user_id)
        items = [
            AccountDetailItem(**raw)
            for raw in get_mydata_institution_section(user_id, org_code, "account_detail")
        ]
        return AccountDetailResponse(
            rsp_code="000",
            rsp_msg="정상처리",
            search_timestamp=_now_timestamp(),
            detail_cnt=len(items),
            detail_list=items,
        )

    def get_bank_account_transactions(self, user_id: str, org_code: str) -> AccountTransactionResponse:
        """은행-004: 수신계좌 거래내역 조회 (기관별 호출)."""
        self._require_profile(user_id)
        items = [
            AccountTransactionItem(**raw)
            for raw in get_mydata_institution_section(user_id, org_code, "account_transactions")
        ]
        return AccountTransactionResponse(
            rsp_code="000",
            rsp_msg="정상처리",
            trans_cnt=len(items),
            trans_list=items,
        )

    def get_cards(self, user_id: str) -> CardListResponse:
        """카드-001: 카드 목록 조회."""
        self._require_profile(user_id)
        items = [CardItem(**raw) for raw in get_mydata_section(user_id, "cards")]
        return CardListResponse(
            rsp_code="000",
            rsp_msg="정상처리",
            search_timestamp=_now_timestamp(),
            card_cnt=len(items),
            card_list=items,
        )

    def get_card_approvals(self, user_id: str) -> CardApprovalResponse:
        """카드-008: 국내 승인내역 조회."""
        self._require_profile(user_id)
        items = [
            CardApprovalItem(**raw) for raw in get_mydata_section(user_id, "card_approvals")
        ]
        return CardApprovalResponse(
            rsp_code="000",
            rsp_msg="정상처리",
            approved_cnt=len(items),
            approved_list=items,
        )
