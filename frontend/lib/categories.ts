// URL 슬러그 -> product_type (은행 무관 정규 분류). 백엔드 crawl config의 product_type과
// 값이 일치해야 한다.
export const PRODUCT_TYPE_SLUGS: Record<string, string> = {
  "time-deposit": "정기예금",
  savings: "적금",
  "demand-deposit": "입출금자유예금",
  "foreign-currency": "외화예금",
  housing: "주택청약",
};

export const SLUG_BY_PRODUCT_TYPE: Record<string, string> = Object.fromEntries(
  Object.entries(PRODUCT_TYPE_SLUGS).map(([slug, type]) => [type, slug]),
);
