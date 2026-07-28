# fss 사용 안하면서 현재는 사용 안하는 코드

from fastapi import APIRouter, HTTPException, Query

from app.clients.fss_client import FSSAPIError, FSSClient
from app.schemas.fss.business_loan import Model as BusinessLoanSearchResponse
from app.schemas.fss.company import Model as CompanySearchResponse
from app.schemas.fss.credit_loan import Model as CreditLoanSearchResponse
from app.schemas.fss.deposit import Model as DepositSearchResponse
from app.schemas.fss.mortgage_loan import Model as MortgageLoanSearchResponse
from app.schemas.fss.rent_house_loan import Model as RentHouseLoanSearchResponse
from app.schemas.fss.saving import Model as SavingSearchResponse

router = APIRouter(prefix="/api/fss", tags=["fss"])


@router.get("/companies", response_model=CompanySearchResponse)
def get_companies(
    top_fin_grp: str = Query("020000", alias="topFinGrp"),
    page_no: int = Query(1, alias="pageNo"),
    finance_cd: str | None = Query(None, alias="financeCd"),
) -> CompanySearchResponse:
    try:
        with FSSClient() as client:
            return client.search_companies(top_fin_grp, page_no, finance_cd)
    except FSSAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/deposits", response_model=DepositSearchResponse)
def get_deposits(
    top_fin_grp: str = Query("020000", alias="topFinGrp"),
    page_no: int = Query(1, alias="pageNo"),
    finance_cd: str | None = Query(None, alias="financeCd"),
) -> DepositSearchResponse:
    try:
        with FSSClient() as client:
            return client.search_deposit_products(top_fin_grp, page_no, finance_cd)
    except FSSAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/savings", response_model=SavingSearchResponse)
def get_savings(
    top_fin_grp: str = Query("020000", alias="topFinGrp"),
    page_no: int = Query(1, alias="pageNo"),
    finance_cd: str | None = Query(None, alias="financeCd"),
) -> SavingSearchResponse:
    try:
        with FSSClient() as client:
            return client.search_saving_products(top_fin_grp, page_no, finance_cd)
    except FSSAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/mortgage-loans", response_model=MortgageLoanSearchResponse)
def get_mortgage_loans(
    top_fin_grp: str = Query("020000", alias="topFinGrp"),
    page_no: int = Query(1, alias="pageNo"),
    finance_cd: str | None = Query(None, alias="financeCd"),
) -> MortgageLoanSearchResponse:
    try:
        with FSSClient() as client:
            return client.search_mortgage_loan_products(top_fin_grp, page_no, finance_cd)
    except FSSAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/rent-house-loans", response_model=RentHouseLoanSearchResponse)
def get_rent_house_loans(
    top_fin_grp: str = Query("020000", alias="topFinGrp"),
    page_no: int = Query(1, alias="pageNo"),
    finance_cd: str | None = Query(None, alias="financeCd"),
) -> RentHouseLoanSearchResponse:
    try:
        with FSSClient() as client:
            return client.search_rent_house_loan_products(top_fin_grp, page_no, finance_cd)
    except FSSAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/credit-loans", response_model=CreditLoanSearchResponse)
def get_credit_loans(
    top_fin_grp: str = Query("020000", alias="topFinGrp"),
    page_no: int = Query(1, alias="pageNo"),
    finance_cd: str | None = Query(None, alias="financeCd"),
) -> CreditLoanSearchResponse:
    try:
        with FSSClient() as client:
            return client.search_credit_loan_products(top_fin_grp, page_no, finance_cd)
    except FSSAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/business-loans", response_model=BusinessLoanSearchResponse)
def get_business_loans(
    top_fin_grp: str = Query("020000", alias="topFinGrp"),
    page_no: int = Query(1, alias="pageNo"),
    finance_cd: str | None = Query(None, alias="financeCd"),
) -> BusinessLoanSearchResponse:
    try:
        with FSSClient() as client:
            return client.search_business_loan_products(top_fin_grp, page_no, finance_cd)
    except FSSAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
