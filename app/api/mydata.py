from fastapi import APIRouter, Depends, Header, HTTPException

from app.clients.mydata.auth import MyDataAuthError, issue_token, resolve_user_id
from app.clients.mydata.client import MyDataError
from app.schemas import AssetDistributionSignal, LiquiditySignal, TokenRequest, TokenResponse, UserSignals
from app.services.mydata.asset_distribution import get_asset_distribution_signal
from app.services.mydata.liquidity import get_liquidity_signal
from app.services.mydata.user_signals import get_user_signals

router = APIRouter(prefix="/api/mydata", tags=["mydata"])


@router.post("/token", response_model=TokenResponse)
def issue_mydata_token(payload: TokenRequest) -> TokenResponse:
    """실제 마이데이터 인가 없이 무조건 토큰을 발급한다 (목업)."""
    return TokenResponse(access_token=issue_token(payload.user_id))


def get_current_user_id(authorization: str = Header(...)) -> str:
    """Authorization 헤더의 Bearer 토큰에서 user_id를 추출한다.

    서명/만료 검증은 하지 않는다 — 토큰 형식만 맞으면 통과시키는 목업 인증.
    """
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Authorization: Bearer <token> 형식이 필요합니다.")
    try:
        return resolve_user_id(token)
    except MyDataAuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.get("/me", response_model=UserSignals)
def get_my_signals(user_id: str = Depends(get_current_user_id)) -> UserSignals:
    """확인용: 유동성 + 자산분포를 한 번에 묶은 전체 신호."""
    try:
        return get_user_signals(user_id)
    except MyDataError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/liquidity", response_model=LiquiditySignal)
def get_my_liquidity(user_id: str = Depends(get_current_user_id)) -> LiquiditySignal:
    """확인용: 현금흐름 & 유동성 집계 신호."""
    try:
        return get_liquidity_signal(user_id)
    except MyDataError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/asset-distribution", response_model=AssetDistributionSignal)
def get_my_asset_distribution(user_id: str = Depends(get_current_user_id)) -> AssetDistributionSignal:
    """확인용: 금융사별 자산 분포 & 만기 집계 신호."""
    try:
        return get_asset_distribution_signal(user_id)
    except MyDataError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
