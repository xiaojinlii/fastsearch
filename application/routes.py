from fastapi import FastAPI

from modules.fastsearch.routes import router as fastsearch_router


def register_routes(app: FastAPI):
    """
    注册路由
    """

    app.include_router(fastsearch_router, prefix="/knowledge_base", tags=["知识库管理"])
