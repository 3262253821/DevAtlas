from fastapi.middleware.cors import CORSMiddleware

from fastapi import FastAPI

from app.core.config import settings
from app.db.session import check_database_connection
from app.routers.auth import router as auth_router
from app.routers.knowledge_base import (
    router as knowledge_base_router
)
from app.routers.documents import (
    router as documents_router
)
from app.routers.retrieval import (
    router as retrieval_router
)
from app.routers.qa import router as qa_router
from app.routers.incidents import (
    router as incidents_router
)


app = FastAPI(
    title="DevAtlas API",
    version="0.1.0",
)

app.add_middleware(
    # CORS中间件，允许跨域请求，用于开发环境
    # 中间件可理解为：请求进入具体路由之前，以及响应返回浏览器之前，统一经过的一层处理
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    # 表示允许浏览器携带凭证
    allow_credentials=True,
    # 允许所有请求方法
    allow_methods=["*"],
    # 允许所有请求头
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(knowledge_base_router)
app.include_router(documents_router)
app.include_router(retrieval_router)
app.include_router(qa_router)
app.include_router(incidents_router)


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