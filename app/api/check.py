from fastapi import APIRouter, HTTPException

from app.schemas import CheckRequest, CheckResponse
from app.services.catalog import get_check_subject
from app.services.rag.pipeline import generate_risk_report
from app.services.store import mydata_user_exists

router = APIRouter(prefix="/api", tags=["check"])


@router.post("/check", response_model=CheckResponse)
def check_product(payload: CheckRequest) -> CheckResponse:
    if not mydata_user_exists(payload.user_id):
        raise HTTPException(status_code=404, detail="User not found")

    subject = get_check_subject(payload.product_id)
    if subject is None:
        raise HTTPException(status_code=404, detail="Product not found")

    return generate_risk_report(subject, payload.user_id)
