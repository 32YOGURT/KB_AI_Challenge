# Fin-Guard AI — 프로젝트 기획서

> KB AI Challenge 해커톤 프로젝트. 이 문서는 기획/아키텍처/기술스택 정리본이며, 세션이 바뀌어도 컨텍스트를 빠르게 복원하기 위한 용도.

## 1. 개요 & 개발 배경 (Problem & Target)

**Target**: 약관을 꼼꼼히 읽을 시간이 없고 금융 지식이 부족한 사회 초년생

**Problem**

- '최고 연 6%' 같은 금리 숫자에 낚여 빽빽한 약관 뒤의 우대 조건 미달, 중도 해지 불이익, 페널티 조항을 알지 못한 채 [가입하기] 버튼을 누름.
- 기존 AI/검색 서비스는 소비자가 무엇이 위험한지 미리 알고 질문해야만 대답해 주므로, 가입 직전의 소비자를 보호하지 못함.

**Solution**

- 금융 포털('금융상품 한눈에' 등)이나 금융 앱에서 [가입하기]를 누르는 순간, AI가 선제적으로(Proactive) 팝업을 띄워 유저 자산/소비 패턴 기반의 '3줄 위험성 팩트체크 리포트'만 깔끔하게 제공.
- 대체 상품 추천 등 군더더기 없이 '최종 점검'에만 집중.

## 2. 핵심 UX & 시연 시나리오 (User Journey)

똑같은 금융 상품을 선택하더라도 유저의 재무/소비 데이터(Mock)에 따라 AI 경고 내용이 다이내믹하게 변경됨.

```
[가짜 금융 포털: "KB청년도약적금" 선택 후 가입하기 클릭]
                            │
                            ▼
           [Fin-Guard AI Engine 3초 스캔]
                            │
       ┌────────────────────┴────────────────────┐
       ▼                                          ▼
[유저 A: 비상금 부족 (잔고 30만원)]        [유저 B: 택시 위주 이용 (지하철 실적 0)]
       │                                          │
       ▼                                          ▼
🚨 RED WARNING                             🟡 YELLOW WARNING
"6개월 내 급전 필요 시 해지하면              "버스/지하철 실적 미달로
 이자 15만원 전액 증발 위험!"                우대금리(1.5%p) 달성 불가!"
       │                                          │
       └────────────────────┬─────────────────────┘
                             ▼
        [ ◀️ 다시 생각하기 ]  [ 위험 감수하고 가입 ➔ ]
```

## 3. 백엔드 & AI 아키텍처 (Technical Architecture)

금감원 공공 API 데이터와 로컬 RAG, 그리고 Web Search Tool이 유기적으로 결합된 하이브리드 자율 판단 에이전트 구조.

```
[프론트엔드: 가입하기 클릭 (상품 ID + 유저 ID)]
                      │
                      ▼
[FastAPI 백엔드 파이프라인]
  ├── 1. 유저 데이터 수집: mock_user.json (월 소득, 비상금, 카테고리별 카드 실적)
  ├── 2. 금감원 오픈 API: 해당 상품의 기본 조건 (우대조건, 유의사항 등) 가져오기
  │
  ├── 3. RAG Retrieval (Primary Engine)
  │      └── 로컬 Vector DB / JSON에서 해당 상품의 [세부 약관 조항 텍스트] 핀포인트 추출
  │
  ├── 4. Self-Correcting Fallback (RAG Miss 시)
  │      └── DB에 세부 조항이 없거나 부족할 경우 ──► [Tavily Web Search Tool] 자율 실행
  │
  └── 5. Context-Aware LLM Inference (GPT-4o-mini)
         └── 약관 조항 + 유저 소비 데이터 결합 추론 ──► Strict JSON Format 출력
                      │
                      ▼
[프론트엔드: 가입 직전 3줄 경고 팝업 모달 UI 렌더링]
```

## 4. 기술 스택 & 데이터 수집 전략 (Tech Stack)

### 🛠️ Tech Stack

- **Frontend**: Next.js / React, Tailwind CSS
- **Backend**: Python FastAPI, LangChain, OpenAI API (gpt-4o-mini)
- **Search / RAG**: Tavily Search API (Fallback용, 아직 미정) · Qdrant (RAG용 Vector DB, `docker-compose.yml`로 로컬 구동)

### 📊 Data Strategy (해커톤 최적화)

- **유저 데이터**: `user_profiles.json` (유저 A: 비상금 부족 / 유저 B: 카드 실적 미달)
- **상품 데이터**: 금융감독원 금융상품통합비교공시 API (기본 정보) + 시연용 대표 상품 3개 약관 텍스트 (RAG DB)

## 5. 기술적 메리트 (Technical Highlights)

**RAG + Web Search Fallback 아키텍처**

- RAG 기반 고속 검색(0.5초)을 기본으로 하되, DB 미등록 상품이나 세부 특약은 Agent가 스스로 판단하여 웹 검색 Tool을 호출하는 Self-Correcting 구조 구현.

**비정형 약관 + 정형 유저 데이터의 추론적 결합**

- 단순 조건문(If-Else)으로는 불가능한 비정형 법률/금융 약관 문맥을 해석하고, 유저의 실시간 소비 맥락과 결합해 위험 수준을 자율 판정.

**Structured Output (Strict JSON) & Guardrails**

- 금융 서비스 특성상 환각(Hallucination)을 제어하기 위해 근거 조항 기반의 strict JSON Schema 출력을 강제하여 백엔드/프론트엔드 연동 안정성 확보.

## 6. 심사위원 Q&A 예상 방어 (Winning Points)

**Q. 실제 유저 데이터는 어디서 가져오나요?**
A. 실제 운영 시에는 '금융 마이데이터 표준 API'에서 수집되는 규격을 그대로 따르며, 데모 환경에서는 마이데이터 인가 제약상 동일한 규격의 Mock JSON 데이터로 대체했습니다.

**Q. 약관 데이터를 매번 실시간으로 파싱하나요?**
A. 실시간 파싱은 속도가 느려 UX를 해치므로, 공공 API 및 RAG DB에 미리 정제된 약관을 0.5초 만에 검색(Retrieval)해 오며, 정보가 부족한 예외 상황에서만 자율 웹 검색 Tool(Fallback)을 활용하도록 속도와 정확도를 모두 잡았습니다.

## 작업 시 참고

- 의존성 설치는 사용자가 직접 실행함 — `requirements.txt`만 갱신하고 `pip install` 등은 직접 실행하지 말 것.
