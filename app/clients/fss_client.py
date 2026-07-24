"""금융감독원 금융상품통합비교공시 Open API 클라이언트.

Host: http://finlife.fss.or.kr
공통 요청 변수: auth(인증키), topFinGrpNo(권역코드), pageNo(페이지 번호), financeCd(금융회사 코드 또는 이름, optional)
응답 포맷: JSON 고정 (경로에 .json 확장자 사용)

엔드포인트별 응답은 app/schemas/fss/*에 정의된 모델로 검증해 반환한다.
"""

from __future__ import annotations

from typing import TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from app.config import FSS_API_KEY
from app.schemas.fss.business_loan import Model as BusinessLoanSearchResponse
from app.schemas.fss.company import Model as CompanySearchResponse
from app.schemas.fss.credit_loan import Model as CreditLoanSearchResponse
from app.schemas.fss.deposit import Model as DepositSearchResponse
from app.schemas.fss.mortgage_loan import Model as MortgageLoanSearchResponse
from app.schemas.fss.rent_house_loan import Model as RentHouseLoanSearchResponse
from app.schemas.fss.saving import Model as SavingSearchResponse

HOST = "https://finlife.fss.or.kr"

T = TypeVar("T", bound=BaseModel)


class FSSAPIError(Exception):
    """FSS API 요청/응답 오류."""


class FSSClient:
    def __init__(self, api_key: str | None = None, host: str = HOST, timeout: float = 10.0) -> None:
        self._api_key = api_key or FSS_API_KEY
        if not self._api_key:
            raise FSSAPIError("FSS_API_KEY가 설정되지 않았습니다 (.env 확인).")
        self._client = httpx.Client(base_url=host.rstrip("/"), timeout=timeout, follow_redirects=True)

    def close(self) -> None:    
        self._client.close()

    def __enter__(self) -> "FSSClient":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def _request(
        self,
        path: str,
        response_model: type[T],
        top_fin_grp: str,
        page_no: int = 1,
        finance_cd: str | None = None,
        **extra_params: object,
    ) -> T:
        """공통 파라미터(auth, topFinGrpNo, pageNo, financeCd)를 붙여 GET 요청 후 response_model로 검증해 반환한다."""
        url_path = path if path.endswith(".json") else f"{path}.json"
        params = {
            "auth": self._api_key,
            "topFinGrpNo": top_fin_grp,
            "pageNo": page_no,
            **extra_params,
        }
        if finance_cd is not None:
            params["financeCd"] = finance_cd
        try:
            response = self._client.get(url_path, params=params)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise FSSAPIError(f"FSS API 요청 실패: {path} ({exc})") from exc

        try:
            payload = response.json()
        except ValueError as exc:
            raise FSSAPIError(
                f"FSS API 응답이 JSON이 아님: {path} status={response.status_code} body={response.text[:500]!r}"
            ) from exc

        try:
            return response_model.model_validate(payload)
        except ValidationError as exc:
            raise FSSAPIError(f"FSS API 응답 검증 실패: {path} ({exc})") from exc

    def search_companies(
        self, top_fin_grp: str, page_no: int = 1, finance_cd: str | None = None, **extra_params: object
    ) -> CompanySearchResponse:
        """금융회사 목록 조회."""
        return self._request(
            "/finlifeapi/companySearch",
            CompanySearchResponse,
            top_fin_grp,
            page_no,
            finance_cd,
            **extra_params,
        )

    def search_deposit_products(
        self, top_fin_grp: str, page_no: int = 1, finance_cd: str | None = None, **extra_params: object
    ) -> DepositSearchResponse:
        """정기예금 상품 조회."""
        return self._request(
            "/finlifeapi/depositProductsSearch",
            DepositSearchResponse,
            top_fin_grp,
            page_no,
            finance_cd,
            **extra_params,
        )

    def search_saving_products(
        self, top_fin_grp: str, page_no: int = 1, finance_cd: str | None = None, **extra_params: object
    ) -> SavingSearchResponse:
        """적금 상품 조회."""
        return self._request(
            "/finlifeapi/savingProductsSearch",
            SavingSearchResponse,
            top_fin_grp,
            page_no,
            finance_cd,
            **extra_params,
        )

    def search_mortgage_loan_products(
        self, top_fin_grp: str, page_no: int = 1, finance_cd: str | None = None, **extra_params: object
    ) -> MortgageLoanSearchResponse:
        """주택담보대출 상품 조회."""
        return self._request(
            "/finlifeapi/mortgageLoanProductsSearch",
            MortgageLoanSearchResponse,
            top_fin_grp,
            page_no,
            finance_cd,
            **extra_params,
        )

    def search_rent_house_loan_products(
        self, top_fin_grp: str, page_no: int = 1, finance_cd: str | None = None, **extra_params: object
    ) -> RentHouseLoanSearchResponse:
        """전세자금대출 상품 조회."""
        return self._request(
            "/finlifeapi/rentHouseLoanProductsSearch",
            RentHouseLoanSearchResponse,
            top_fin_grp,
            page_no,
            finance_cd,
            **extra_params,
        )

    def search_credit_loan_products(
        self, top_fin_grp: str, page_no: int = 1, finance_cd: str | None = None, **extra_params: object
    ) -> CreditLoanSearchResponse:
        """개인신용대출 상품 조회."""
        return self._request(
            "/finlifeapi/creditLoanProductsSearch",
            CreditLoanSearchResponse,
            top_fin_grp,
            page_no,
            finance_cd,
            **extra_params,
        )

    def search_business_loan_products(
        self, top_fin_grp: str, page_no: int = 1, finance_cd: str | None = None, **extra_params: object
    ) -> BusinessLoanSearchResponse:
        """개인사업자대출 상품 조회."""
        return self._request(
            "/finlifeapi/busiLoanProductsSearch",
            BusinessLoanSearchResponse,
            top_fin_grp,
            page_no,
            finance_cd,
            **extra_params,
        )
