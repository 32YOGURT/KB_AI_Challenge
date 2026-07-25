from fastapi import APIRouter, HTTPException

from app.schemas import CheckRequest, CheckResponse
from app.services.rag.pipeline import generate_risk_report
from app.services.store import get_product, mydata_user_exists

router = APIRouter(prefix="/api", tags=["check"])


@router.post("/check", response_model=CheckResponse)
def check_product(payload: CheckRequest) -> CheckResponse:
    product = get_product(payload.product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    if not mydata_user_exists(payload.user_id):
        raise HTTPException(status_code=404, detail="User not found")

    return generate_risk_report(product, payload.user_id)
