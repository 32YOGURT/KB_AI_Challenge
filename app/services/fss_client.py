"""금융감독원 금융상품통합비교공시 Open API 공통 베이스라인 클라이언트.

Base URL: http://finlife.fss.or.kr/finlifeapi
공통 요청 변수: auth(인증키), topFinGrp(권역코드), pageNo(페이지 번호)
응답 포맷: JSON 고정

엔드포인트별 파라미터/응답 스키마는 이 클라이언트의 get()을 통해
각 엔드포인트 전용 함수(예: get_deposit_products)에서 다룬다.
"""

from __future__ import annotations

import httpx

from app.config import FSS_API_KEY

BASE_URL = "http://finlife.fss.or.kr/finlifeapi"


class FSSAPIError(Exception):
    """FSS API 요청/응답 오류."""


class FSSClient:
    def __init__(self, api_key: str | None = None, base_url: str = BASE_URL, timeout: float = 10.0) -> None:
        self._api_key = api_key or FSS_API_KEY
        if not self._api_key:
            raise FSSAPIError("FSS_API_KEY가 설정되지 않았습니다 (.env 확인).")
        self._client = httpx.Client(base_url=base_url.rstrip("/"), timeout=timeout)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "FSSClient":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def get(self, endpoint: str, top_fin_grp: str, page_no: int = 1, **extra_params: object) -> dict:
        """공통 파라미터(auth, topFinGrp, pageNo)를 붙여 GET 요청 후 JSON을 반환한다.

        endpoint: "companySearchApi.json" 형태의 파일명 (선행 슬래시 불필요).
        extra_params: 엔드포인트 고유 파라미터 (예: finGrpNo).
        """
        params = {
            "auth": self._api_key,
            "topFinGrp": top_fin_grp,
            "pageNo": page_no,
            **extra_params,
        }
        try:
            response = self._client.get(f"/{endpoint.lstrip('/')}", params=params)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise FSSAPIError(f"FSS API 요청 실패: {endpoint} ({exc})") from exc

        return response.json()
