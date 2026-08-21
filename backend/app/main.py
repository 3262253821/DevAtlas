from fastapi import FastAPI

from app.core.config import settings
from app.db.session import check_database_connection


app = FastAPI(
    title="DevAtlas API",
    version="0.1.0",
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "dev-atlas-api",
        "environment": settings.app_env,
    }


@app.get("/health/db")
def database_health_check() -> dict[str, str]:
    check_database_connection()

    return {
        "status": "ok",
        "database": "mysql",
    }