from fastapi import FastAPI

from app.core.config import settings
from app.db.session import check_database_connection
from app.routers.auth import router as auth_router
from app.routers.knowledge_base import router as knowledge_base_router
from app.routers.documents import router as documents_router
from app.routers.retrieval import router as retrieval_router
from app.routers.qa import router as qa_router

app = FastAPI(
    title="DevAtlas API",
    version="0.1.0",
)

app.include_router(auth_router)
app.include_router(knowledge_base_router)
app.include_router(documents_router)
app.include_router(retrieval_router)
app.include_router(qa_router)

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