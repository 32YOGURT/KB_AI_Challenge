from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import catalog, check, documents, mydata, users
from app.config import ALLOWED_ORIGINS

app = FastAPI(title="Fin-Guard AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_origins=ALLOWED_ORIGINS,
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
