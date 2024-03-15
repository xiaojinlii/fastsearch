"""
官方文档——中间件：https://fastapi.tiangolo.com/tutorial/middleware/
官方文档——高级中间件：https://fastapi.tiangolo.com/advanced/middleware/
"""

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from application import settings
from core.utils import import_functions


def register_middlewares(app: FastAPI):
    """
    注册中间件
    """

    import_functions(settings.MIDDLEWARES, "中间件", app=app)

    # 跨域解决
    if settings.CORS_ORIGIN_ENABLE:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.ALLOW_ORIGINS,
            allow_credentials=settings.ALLOW_CREDENTIALS,
            allow_methods=settings.ALLOW_METHODS,
            allow_headers=settings.ALLOW_HEADERS
        )
