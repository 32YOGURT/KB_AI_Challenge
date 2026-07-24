from pydantic import BaseModel


class UserProfile(BaseModel):
    id: str
    display_name: str
    monthly_income: float
    emergency_fund: float
    monthly_transit_count: int
    monthly_taxi_count: int
