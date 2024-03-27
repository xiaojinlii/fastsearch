from fastapi import FastAPI

from modules.fastsearch.routes import router as fastsearch_router
from modules.fastsearch.routes_tlbb import router as fastsearch_tlbb_router


def register_routes(app: FastAPI):
    """
    注册路由
    """

    app.include_router(fastsearch_router, prefix="/knowledge_base", tags=["知识库管理"])
    app.include_router(fastsearch_tlbb_router, prefix="/knowledge_base", tags=["知识库管理"])
