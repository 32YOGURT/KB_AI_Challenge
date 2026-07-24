from fastapi import APIRouter, HTTPException

from app.schemas import CheckRequest, CheckResponse
from app.services.risk_engine import generate_risk_report
from app.services.store import get_product, get_user_profile

router = APIRouter(prefix="/api", tags=["check"])


@router.post("/check", response_model=CheckResponse)
def check_product(payload: CheckRequest) -> CheckResponse:
    product = get_product(payload.product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    user = get_user_profile(payload.user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return generate_risk_report(product, user)
