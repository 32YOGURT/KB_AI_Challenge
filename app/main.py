from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import catalog, check, documents, mydata, users

app = FastAPI(title="Fin-Guard AI API")

app.add_middleware(
    CORSMiddleware,
    # worktree를 여러 개 띄우면 Next dev 서버가 3001, 3002...로 밀려서 포트를 고정할 수 없다.
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(catalog.router)
app.include_router(check.router)
app.include_router(documents.router)
app.include_router(mydata.router)
app.include_router(users.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
