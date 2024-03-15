"""
FastApi 更新文档：https://github.com/tiangolo/fastapi/releases
FastApi Github：https://github.com/tiangolo/fastapi
Typer 官方文档：https://typer.tiangolo.com/
"""

import asyncio
from fastapi import FastAPI
import uvicorn
from application import settings
from application.routes import register_routes
from core.docs import custom_api_docs
from core.event import lifespan
from core.exception import register_exception
from core.middleware import register_middlewares
from core.mounting import register_mounting
from db.migrate import create_tables
import typer

shell_app = typer.Typer()


def create_app():
    """
    启动项目

    docs_url：配置交互文档的路由地址，如果禁用则为None，默认为 /docs
    redoc_url： 配置 Redoc 文档的路由地址，如果禁用则为None，默认为 /redoc
    openapi_url：配置接口文件json数据文件路由地址，如果禁用则为None，默认为/openapi.json
    """
    app = FastAPI(
        title=settings.TITLE,
        description=settings.DESCRIPTION,
        version=settings.VERSION,
        lifespan=lifespan,
        docs_url=None,
        redoc_url=None
    )

    # 注册中间件
    register_middlewares(app)
    # 全局异常捕捉处理
    register_exception(app)
    # 注册路由
    register_routes(app)
    # 配置接口文档静态资源
    custom_api_docs(app)
    # 挂载文件目录
    register_mounting(app)

    return app


@shell_app.command()
def run(
        host: str = typer.Option(default=settings.HOST, help='监听主机IP，默认开放给本网络所有主机'),
        port: int = typer.Option(default=settings.PORT, help='监听端口'),
        workers: int = typer.Option(default=settings.WORKERS, help='工作进程数')
):
    """
    启动项目

    factory: 在使用 uvicorn.run() 启动 ASGI 应用程序时，可以通过设置 factory 参数来指定应用程序工厂。
    应用程序工厂是一个返回 ASGI 应用程序实例的可调用对象，它可以在启动时动态创建应用程序实例。
    """
    uvicorn.run(app='main:create_app', host=host, port=port, lifespan="on", factory=True, workers=workers)


@shell_app.command()
def init():
    """
    初始化数据库
    需要迁移到数据库的模型 要在application/configs/database_config.py的MIGRATE_MODELS里配置
    """
    asyncio.run(create_tables())
    print("数据库初始化完成！")


if __name__ == '__main__':
    shell_app()
