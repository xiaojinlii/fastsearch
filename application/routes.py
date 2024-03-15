from fastapi import FastAPI

# from modules.quickstart.routes import router as quickstart_router
from modules.fastsearch.routes import router as fastsearch_router


def register_routes(app: FastAPI):
    """
    注册路由
    """

    # app.include_router(quickstart_router, prefix="/quickstart", tags=["快速开始"])
    app.include_router(fastsearch_router, prefix="/knowledge_base", tags=["知识库管理"])
