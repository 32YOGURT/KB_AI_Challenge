# 빌드 컨텍스트는 repo 루트 (requirements.txt, app/ 를 같이 COPY해야 해서).
# deploy/docker-compose.yml에서 build.context: .. 로 지정한다.
FROM python:3.13-slim

WORKDIR /srv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
