# 빌드 컨텍스트는 repo 루트 (requirements.txt, app/ 를 같이 COPY해야 해서).
# deploy/docker-compose.yml에서 build.context: .. 로 지정한다.
FROM python:3.13-slim

WORKDIR /srv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
# 상품 카탈로그(app/services/catalog.py가 런타임에 읽음). 없으면 /api/catalog, /api/check가
# 전부 죽는다 — 캐시 디렉터리는 빼고 manifest만 넣는다.
COPY crawled_data/manifest.json ./crawled_data/manifest.json

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
