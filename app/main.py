from fastapi import FastAPI
from sqlalchemy import text

from app.api.v1 import admin, auth
from app.config import settings
from app.database import engine

app = FastAPI(title=settings.APP_NAME)

app.include_router(auth.router)
app.include_router(admin.router)


@app.get("/health")
def health():
    return {"status": "ok", "environment": settings.ENVIRONMENT}


@app.get("/health/database")
def health_database():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as exc:  # noqa: BLE001 - surfaced intentionally for a health probe
        return {"status": "error", "detail": str(exc)}
