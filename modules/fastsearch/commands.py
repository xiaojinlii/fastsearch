import asyncio
import typer


sqlalchemy_typer = typer.Typer(no_args_is_help=True, add_completion=False)


@sqlalchemy_typer.command()
def create_tables():
    """
    初始化数据库
    需要迁移到数据库的模型 要在application/configs/database_config.py的MIGRATE_MODELS里配置
    """
    from .knowledge_base_manager.db.migrate import create_tables as migrate_create_tables
    from xiaoapi.conf import settings

    migrate_create_tables()
    print(f"数据库表结构创建成功！DATABASE_URL: {settings.SQLALCHEMY_DATABASE_URL_SYNC}")
