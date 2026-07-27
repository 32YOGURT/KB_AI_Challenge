from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import catalog, check, mydata, users

app = FastAPI(title="Fin-Guard AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(catalog.router)
app.include_router(check.router)
app.include_router(mydata.router)
app.include_router(users.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
