from fastapi import APIRouter, HTTPException, Query

from app.clients.fss_client import FSSAPIError, FSSClient
from app.schemas import UserSummary
from app.schemas.fss.normalized import (
    NormalizedBusinessLoan,
    NormalizedCompany,
    NormalizedCreditLoan,
    NormalizedDeposit,
    NormalizedMortgageLoan,
    NormalizedRentHouseLoan,
    NormalizedSaving,
)
from app.services.fss.normalize import (
    normalize_business_loans,
    normalize_companies,
    normalize_credit_loans,
    normalize_deposits,
    normalize_mortgage_loans,
    normalize_rent_house_loans,
    normalize_savings,
)
from app.services.store import list_mydata_users

router = APIRouter(prefix="/api", tags=["products"])


@router.get("/products/deposits", response_model=list[NormalizedDeposit])
def get_deposit_products(
    top_fin_grp: str = Query("020000", alias="topFinGrp"),
    page_no: int = Query(1, alias="pageNo"),
    finance_cd: str | None = Query(None, alias="financeCd"),
) -> list[NormalizedDeposit]:
    try:
        with FSSClient() as client:
            return normalize_deposits(client.search_deposit_products(top_fin_grp, page_no, finance_cd))
    except FSSAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/products/savings", response_model=list[NormalizedSaving])
def get_saving_products(
    top_fin_grp: str = Query("020000", alias="topFinGrp"),
    page_no: int = Query(1, alias="pageNo"),
    finance_cd: str | None = Query(None, alias="financeCd"),
) -> list[NormalizedSaving]:
    try:
        with FSSClient() as client:
            return normalize_savings(client.search_saving_products(top_fin_grp, page_no, finance_cd))
    except FSSAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/products/mortgage-loans", response_model=list[NormalizedMortgageLoan])
def get_mortgage_loan_products(
    top_fin_grp: str = Query("020000", alias="topFinGrp"),
    page_no: int = Query(1, alias="pageNo"),
    finance_cd: str | None = Query(None, alias="financeCd"),
) -> list[NormalizedMortgageLoan]:
    try:
        with FSSClient() as client:
            return normalize_mortgage_loans(client.search_mortgage_loan_products(top_fin_grp, page_no, finance_cd))
    except FSSAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/products/rent-house-loans", response_model=list[NormalizedRentHouseLoan])
def get_rent_house_loan_products(
    top_fin_grp: str = Query("020000", alias="topFinGrp"),
    page_no: int = Query(1, alias="pageNo"),
    finance_cd: str | None = Query(None, alias="financeCd"),
) -> list[NormalizedRentHouseLoan]:
    try:
        with FSSClient() as client:
            return normalize_rent_house_loans(
                client.search_rent_house_loan_products(top_fin_grp, page_no, finance_cd)
            )
    except FSSAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/products/credit-loans", response_model=list[NormalizedCreditLoan])
def get_credit_loan_products(
    top_fin_grp: str = Query("020000", alias="topFinGrp"),
    page_no: int = Query(1, alias="pageNo"),
    finance_cd: str | None = Query(None, alias="financeCd"),
) -> list[NormalizedCreditLoan]:
    try:
        with FSSClient() as client:
            return normalize_credit_loans(client.search_credit_loan_products(top_fin_grp, page_no, finance_cd))
    except FSSAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/products/business-loans", response_model=list[NormalizedBusinessLoan])
def get_business_loan_products(
    top_fin_grp: str = Query("020000", alias="topFinGrp"),
    page_no: int = Query(1, alias="pageNo"),
    finance_cd: str | None = Query(None, alias="financeCd"),
) -> list[NormalizedBusinessLoan]:
    try:
        with FSSClient() as client:
            return normalize_business_loans(client.search_business_loan_products(top_fin_grp, page_no, finance_cd))
    except FSSAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/products/companies", response_model=list[NormalizedCompany])
def get_company_products(
    top_fin_grp: str = Query("020000", alias="topFinGrp"),
    page_no: int = Query(1, alias="pageNo"),
    finance_cd: str | None = Query(None, alias="financeCd"),
) -> list[NormalizedCompany]:
    try:
        with FSSClient() as client:
            return normalize_companies(client.search_companies(top_fin_grp, page_no, finance_cd))
    except FSSAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/users", response_model=list[UserSummary])
def get_users() -> list[UserSummary]:
    return list_mydata_users()
