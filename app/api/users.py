from fastapi import APIRouter

from app.schemas import UserSummary
from app.services.store import list_mydata_users

router = APIRouter(prefix="/api", tags=["users"])


@router.get("/users", response_model=list[UserSummary])
def get_users() -> list[UserSummary]:
    return list_mydata_users()
