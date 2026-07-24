"""금융감독원 금융상품통합비교공시 Open API 클라이언트.

Host: http://finlife.fss.or.kr
공통 요청 변수: auth(인증키), topFinGrp(권역코드), pageNo(페이지 번호)
응답 포맷: JSON 고정 (경로에 .json 확장자 사용)

엔드포인트별 파라미터/응답 스키마는 각 search_* 메서드에서 다룬다.
정기예금(fdrmDpstApi)만 다른 엔드포인트들과 달리 /finlifeapi가 아닌 /finlife 하위에 있다.
"""

from __future__ import annotations

import httpx

from app.config import FSS_API_KEY

HOST = "http://finlife.fss.or.kr"


class FSSAPIError(Exception):
    """FSS API 요청/응답 오류."""


class FSSClient:
    def __init__(self, api_key: str | None = None, host: str = HOST, timeout: float = 10.0) -> None:
        self._api_key = api_key or FSS_API_KEY
        if not self._api_key:
            raise FSSAPIError("FSS_API_KEY가 설정되지 않았습니다 (.env 확인).")
        self._client = httpx.Client(base_url=host.rstrip("/"), timeout=timeout)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "FSSClient":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def _request(self, path: str, top_fin_grp: str, page_no: int = 1, **extra_params: object) -> dict:
        """공통 파라미터(auth, topFinGrp, pageNo)를 붙여 GET 요청 후 JSON을 반환한다."""
        url_path = path if path.endswith(".json") else f"{path}.json"
        params = {
            "auth": self._api_key,
            "topFinGrp": top_fin_grp,
            "pageNo": page_no,
            **extra_params,
        }
        try:
            response = self._client.get(url_path, params=params)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise FSSAPIError(f"FSS API 요청 실패: {path} ({exc})") from exc

        return response.json()

    def search_companies(self, top_fin_grp: str, page_no: int = 1, **extra_params: object) -> dict:
        """금융회사 목록 조회."""
        return self._request("/finlifeapi/companySearch", top_fin_grp, page_no, **extra_params)

    def search_deposit_products(self, top_fin_grp: str, page_no: int = 1, **extra_params: object) -> dict:
        """정기예금 상품 조회."""
        return self._request("/finlife/fdrmDpstApi/list", top_fin_grp, page_no, **extra_params)

    def search_saving_products(self, top_fin_grp: str, page_no: int = 1, **extra_params: object) -> dict:
        """적금 상품 조회."""
        return self._request("/finlifeapi/savingProductsSearch", top_fin_grp, page_no, **extra_params)

    def search_mortgage_loan_products(self, top_fin_grp: str, page_no: int = 1, **extra_params: object) -> dict:
        """주택담보대출 상품 조회."""
        return self._request("/finlifeapi/mortgageLoanProductsSearch", top_fin_grp, page_no, **extra_params)

    def search_rent_house_loan_products(self, top_fin_grp: str, page_no: int = 1, **extra_params: object) -> dict:
        """전세자금대출 상품 조회."""
        return self._request("/finlifeapi/rentHouseLoanProductsSearch", top_fin_grp, page_no, **extra_params)

    def search_credit_loan_products(self, top_fin_grp: str, page_no: int = 1, **extra_params: object) -> dict:
        """개인신용대출 상품 조회."""
        return self._request("/finlifeapi/creditLoanProductsSearch", top_fin_grp, page_no, **extra_params)

    def search_business_loan_products(self, top_fin_grp: str, page_no: int = 1, **extra_params: object) -> dict:
        """개인사업자대출 상품 조회."""
        return self._request("/finlifeapi/busiLoanProductsSearch", top_fin_grp, page_no, **extra_params)
